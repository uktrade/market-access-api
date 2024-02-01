import datetime
import logging
import operator
import urllib.parse
from functools import reduce
from typing import List, Optional
from uuid import uuid4

import django_filters
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
from django.core.validators import int_list_validator
from django.db import models
from django.db.models import CASCADE, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.widgets import BooleanWidget
from hashid_field import HashidAutoField
from notifications_python_client.notifications import NotificationsAPIClient
from simple_history.models import HistoricalRecords

from api.collaboration import models as collaboration_models
from api.commodities.models import Commodity
from api.commodities.utils import format_commodity_code
from api.core.exceptions import ArchivingException
from api.core.models import BaseModel, FullyArchivableMixin
from api.history.v2.service import FieldMapping, get_model_history
from api.metadata import models as metadata_models
from api.metadata import utils as metadata_utils
from api.metadata.constants import (
    AWAITING_REVIEW_FROM,
    BARRIER_ARCHIVED_REASON,
    BARRIER_PENDING,
    BARRIER_SOURCE,
    BARRIER_TERMS,
    GOVERNMENT_ORGANISATION_TYPES,
    NEXT_STEPS_ITEMS_STATUS_CHOICES,
    PRIORITY_LEVELS,
    PROGRESS_UPDATE_CHOICES,
    STAGE_STATUS,
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_CATEGORIES,
    TRADE_DIRECTION_CHOICES,
    TRADING_BLOC_CHOICES,
    TRADING_BLOCS,
    WIDER_EUROPE_REGIONS,
    BarrierStatus,
    PublicBarrierStatus,
)

from . import validators
from .report_stages import REPORT_CONDITIONS, report_stage_status
from .utils import random_barrier_reference

logger = logging.getLogger(__name__)

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH

User = get_user_model()


class Stage(models.Model):
    """Reporting workflow stages"""

    code = models.CharField(max_length=4)
    description = models.CharField(max_length=MAX_LENGTH)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code


class ReportManager(models.Manager):
    """Manage reports within the model, with draft=True"""

    def get_queryset(self):
        return super().get_queryset().filter(Q(draft=True) & Q(archived=False))


class BarrierManager(models.Manager):
    """
    Manage barriers within the model, with draft=False
    Keep archived filter off from here to allow to filter for archived barriers only.
    """

    def get_queryset(self):
        return super().get_queryset().filter(draft=False)


class PublicBarrierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(barrier__draft=False)

    @staticmethod
    def get_or_create_for_barrier(barrier):
        public_barrier, created = PublicBarrier.objects.get_or_create(
            barrier=barrier,
            defaults={
                "status": barrier.status,
                "status_date": barrier.status_date,
                "country": barrier.country,
                "trading_bloc": barrier.trading_bloc,
                "caused_by_trading_bloc": barrier.caused_by_trading_bloc,
                "sectors": barrier.sectors,
                "all_sectors": barrier.all_sectors,
            },
        )
        if created:
            public_barrier.categories.set(barrier.categories.all())

        return public_barrier, created


class BarrierHistoricalModel(models.Model):
    """
    Abstract model for history models tracking category changes.
    """

    categories_cache = ArrayField(
        models.PositiveIntegerField(),
        blank=True,
        default=list,
    )
    commodities_cache = ArrayField(
        models.JSONField(),
        blank=True,
        default=list,
    )
    tags_cache = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
    )
    organisations_cache = ArrayField(
        models.IntegerField(),
        blank=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if set(self.categories_cache or []) != set(old_history.categories_cache or []):
            changed_fields.add("categories")

        commodity_codes = [c.get("code") for c in self.commodities_cache]
        old_commodity_codes = [c.get("code") for c in old_history.commodities_cache]
        if set(commodity_codes) != set(old_commodity_codes):
            changed_fields.add("commodities")

        if set(self.tags_cache or []) != set(old_history.tags_cache or []):
            changed_fields.add("tags")

        if set(self.organisations_cache or []) != set(
            old_history.organisations_cache or []
        ):
            changed_fields.add("organisations")

        if changed_fields.intersection(("country", "admin_areas")):
            changed_fields.discard("country")
            changed_fields.discard("admin_areas")
            changed_fields.add("location")

        if "caused_by_trading_bloc" in changed_fields:
            if self.caused_by_trading_bloc or old_history.caused_by_trading_bloc:
                changed_fields.add("location")

        if "trading_bloc" in changed_fields:
            changed_fields.discard("trading_bloc")
            changed_fields.add("location")

        if "all_sectors" in changed_fields:
            changed_fields.discard("all_sectors")
            changed_fields.add("sectors")

        return list(changed_fields)

    def update_categories(self):
        self.categories_cache = list(
            self.instance.categories.values_list("id", flat=True)
        )

    def update_commodities(self):
        self.commodities_cache = []
        for barrier_commodity in self.instance.barrier_commodities.all():
            item = {
                "code": barrier_commodity.code,
                "country": None,
                "trading_bloc": None,
                "commodity": {
                    "code": barrier_commodity.commodity.code,
                    "description": barrier_commodity.commodity.description,
                    "full_description": barrier_commodity.commodity.full_description,
                    "version": barrier_commodity.commodity.version,
                },
            }
            if barrier_commodity.country:
                item["country"] = {"id": str(barrier_commodity.country)}
            elif barrier_commodity.trading_bloc:
                item["trading_bloc"] = {"code": barrier_commodity.trading_bloc}
            self.commodities_cache.append(item)

    def update_tags(self):
        self.tags_cache = list(self.instance.tags.values_list("id", flat=True))

    def update_organisations(self):
        self.organisations_cache = list(
            self.instance.organisations.values_list("id", flat=True)
        )

    def save(self, *args, **kwargs):
        self.update_categories()
        self.update_commodities()
        self.update_tags()
        self.update_organisations()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class BarrierProgressUpdate(FullyArchivableMixin, BaseModel):
    """
    This is now specifically an update relating to a PB100 barrier.
    """

    id = models.UUIDField(primary_key=True, default=uuid4)
    created_on = models.DateTimeField(
        db_index=True, null=True, blank=True, auto_now_add=False
    )
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=False)
    barrier = models.ForeignKey(
        "Barrier", on_delete=models.CASCADE, related_name="progress_updates"
    )
    status = models.CharField(
        choices=PROGRESS_UPDATE_CHOICES, max_length=100, null=True
    )
    update = models.TextField(
        help_text="What has been done to address the barrier?", blank=True, null=True
    )
    next_steps = models.TextField(
        help_text="What next steps are required to address the barrier?",
        blank=True,
        null=True,
    )

    history = HistoricalRecords()

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(barrier__id=barrier_id)
        fields = (["status", "update", "next_steps"],)

        return get_model_history(
            qs,
            model="progress_update",
            fields=fields,
            track_first_item=True,
        )

    class Meta:
        # order by date descending
        ordering = ("-created_on",)
        verbose_name = "Top 100 Barrier Progress Update"
        verbose_name_plural = "Top 100 Barrier Progress Updates"


class ProgrammeFundProgressUpdate(FullyArchivableMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_on = models.DateTimeField(
        db_index=True, null=True, blank=True, auto_now_add=False
    )
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=False)
    barrier = models.ForeignKey(
        "Barrier",
        on_delete=models.CASCADE,
        related_name="programme_fund_progress_updates",
    )
    milestones_and_deliverables = models.TextField(
        help_text="What has been done to address the barrier?", blank=True, null=True
    )
    expenditure = models.TextField(
        help_text="What next steps are required to address the barrier?",
        blank=True,
        null=True,
    )

    history = HistoricalRecords()

    class Meta:
        # order by date descending
        ordering = ("-created_on",)
        verbose_name = "Programme Fund Barrier Progress Update"
        verbose_name_plural = "Programme Fund Barrier Progress Updates"

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(barrier__id=barrier_id)
        fields = ("milestones_and_deliverables", "expenditure")

        return get_model_history(
            qs,
            model="programme_fund_progress_update",
            fields=fields,
            track_first_item=True,
        )


class Barrier(FullyArchivableMixin, BaseModel):
    """Barrier Instance, converted from a completed and accepted Report"""

    id = models.UUIDField(primary_key=True, default=uuid4)
    code = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        null=True,
        unique=True,
        help_text="Readable reference code e.g. B-20-NTZ",
        db_index=True,
    )
    activity_reminder_sent = models.DateTimeField(null=True, blank=True)
    term = models.PositiveIntegerField(
        choices=BARRIER_TERMS,
        blank=True,
        null=True,
        help_text="Is this a short-term procedural or long-term strategic barrier?",
    )
    estimated_resolution_date = models.DateField(
        blank=True, null=True, help_text="Date the barrier ends"
    )
    proposed_estimated_resolution_date = models.DateField(
        blank=True, null=True, help_text="Proposed date the barrier ends"
    )
    proposed_estimated_resolution_date_created = models.DateTimeField(
        blank=True, null=True, help_text="Date in which the proposed date was created"
    )
    proposed_estimated_resolution_date_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="proposed_estimated_resolution_date_user",
        blank=True,
        null=True,
        help_text="User who created the proposed date",
    )
    estimated_resolution_date_change_reason = models.TextField(
        blank=True, null=True, help_text="Reason for proposed date"
    )
    country = models.UUIDField(blank=True, null=True)
    caused_by_admin_areas = models.BooleanField(null=True, blank=True)
    admin_areas = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
        help_text="list of states, provinces, regions etc within a country",
    )
    trading_bloc = models.CharField(
        choices=TRADING_BLOC_CHOICES,
        max_length=7,
        blank=True,
    )
    caused_by_trading_bloc = models.BooleanField(null=True)
    trade_direction = models.SmallIntegerField(
        choices=TRADE_DIRECTION_CHOICES,
        blank=True,
        null=True,
    )
    sectors_affected = models.BooleanField(
        help_text="Does the barrier affect any sectors?",
        null=True,
        blank=True,
    )
    all_sectors = models.BooleanField(
        help_text="Does the barrier affect all sectors?",
        null=True,
        blank=True,
    )
    sectors = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
    )
    main_sector = models.UUIDField(blank=True, null=True)
    companies = models.JSONField(blank=True, null=True)
    related_organisations = models.JSONField(blank=True, null=True)
    product = models.CharField(max_length=MAX_LENGTH, blank=True)
    source = models.CharField(choices=BARRIER_SOURCE, max_length=25, blank=True)
    other_source = models.CharField(max_length=MAX_LENGTH, blank=True)
    title = models.CharField(max_length=MAX_LENGTH, blank=True)
    summary = models.TextField(blank=True)
    is_summary_sensitive = models.BooleanField(
        help_text="Does the summary contain sensitive information?",
        blank=True,
        null=True,
    )

    # next steps will be saved here momentarily during reporting.
    # once the report is ready for submission, this will be added as a new note
    next_steps_summary = models.TextField(blank=True)
    categories = models.ManyToManyField(
        metadata_models.Category, related_name="barriers"
    )
    reported_on = models.DateTimeField(db_index=True, auto_now_add=True)

    # Barrier status
    status = models.PositiveIntegerField(choices=BarrierStatus.choices, default=0)
    sub_status = models.CharField(
        choices=BARRIER_PENDING,
        max_length=25,
        blank=True,
    )
    sub_status_other = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        help_text="Text if sub status is 'OTHER'",
    )
    status_summary = models.TextField(blank=True)
    status_date = models.DateField(
        blank=True,
        null=True,
        help_text=(
            "If resolved or part-resolved, the month and year supplied by the user, "
            "otherwise the current time when the status was set. Records date status "
            "is effective from; resolved statuses are user-set, other statuses are "
            "effective immediately after the status change."
        ),
    )
    commercial_value = models.BigIntegerField(blank=True, null=True)
    commercial_value_explanation = models.TextField(blank=True)
    economic_assessment_eligibility = models.BooleanField(
        blank=True,
        null=True,
        help_text="Is the barrier eligible for an economic assessment?",
    )
    economic_assessment_eligibility_summary = models.TextField(
        blank=True,
        help_text="Why is the barrier eligible/ineligible for an economic assessment?",
    )
    public_eligibility = models.BooleanField(
        blank=True,
        null=True,
        help_text="Mark the barrier as either publishable or unpublishable to the public.",
    )
    public_eligibility_postponed = models.BooleanField(
        blank=True,
        default=False,
        help_text="If public eligibility has been marked to be reviewed later.",
    )
    public_eligibility_summary = models.TextField(
        blank=True,
        help_text="Public eligibility summary if provided by user.",
    )
    top_priority_status = models.CharField(
        blank=True,
        default=TOP_PRIORITY_BARRIER_STATUS.NONE,
        max_length=50,
        choices=TOP_PRIORITY_BARRIER_STATUS,
    )
    top_priority_rejection_summary = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "If an admin rejects a request for top priority,"
            " this is the message that will be displayed to the user."
        ),
    )

    # Legacy priority summary - can be deleted after TSS-515 goes live
    priority_summary = models.TextField(blank=True)

    # Old Barrier priority - keep for legacy use
    priority = models.ForeignKey(
        metadata_models.BarrierPriority,
        default=1,
        related_name="barrier",
        on_delete=models.PROTECT,
    )
    # New barrier priority
    priority_level = models.CharField(
        max_length=20,
        blank=True,
        choices=PRIORITY_LEVELS,
        default=PRIORITY_LEVELS.NONE,
    )
    priority_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    # Todo : this field may become redundant post migration to django-formtools for report workflow
    stages = models.ManyToManyField(
        Stage,
        related_name="report_stages",
        through="BarrierReportStage",
        help_text="Store reporting stages before submitting",
    )
    # Temporary store for session data during barrier creation
    new_report_session_data = models.TextField(blank=True)
    archived_reason = models.CharField(
        choices=BARRIER_ARCHIVED_REASON,
        max_length=25,
        blank=True,
    )
    archived_explanation = models.TextField(blank=True)
    commodities = models.ManyToManyField(Commodity, through="BarrierCommodity")
    trade_category = models.CharField(
        choices=TRADE_CATEGORIES, max_length=32, blank=True
    )
    draft = models.BooleanField(default=True)
    organisations = models.ManyToManyField(
        metadata_models.Organisation,
        help_text="Organisations that are related to the barrier",
    )

    history = HistoricalRecords(bases=[BarrierHistoricalModel])

    tags = models.ManyToManyField(metadata_models.BarrierTag, blank=True)

    completion_percent = models.PositiveIntegerField(
        max_length=3,
        blank=True,
        null=True,
        help_text="Percentage value representing how much information regarding a barrier has been provided",
    )

    start_date = models.DateField(blank=True, null=True)
    is_start_date_known = models.BooleanField(default=False)

    export_types = models.ManyToManyField(
        metadata_models.ExportType,
        blank=True,
    )
    export_description = models.TextField(
        blank=True,
        null=True,
    )

    is_currently_active = models.BooleanField(
        null=True,
        help_text="Is the barrier currently active",
    )

    def __str__(self):
        if self.title is None:
            return self.code
        return self.title

    objects = models.Manager()
    reports = ReportManager()
    barriers = BarrierManager()

    class Meta:
        ordering = ["-reported_on"]
        permissions = [
            (
                "change_barrier_public_eligibility",
                "Can change barrier public eligibility",
            ),
            ("download_barriers", "Can download barriers"),
        ]

    @classmethod
    def get_history(
        cls,
        barrier_id,
        enrich=False,
        fields: Optional[List] = None,
        track_first_item: bool = False,
    ):
        qs = cls.history.filter(id=barrier_id, draft=False)
        default_fields = (
            [
                "archived",
                "archived_reason",
                "archived_explanation",
                "unarchived_reason",
            ],
            [
                "country",
                "trading_bloc",
                "caused_by_trading_bloc",
                "admin_areas",
            ],
            "commercial_value",
            "commercial_value_explanation",
            "companies",
            "economic_assessment_eligibility",
            "economic_assessment_eligibility_summary",
            "estimated_resolution_date",
            "start_date",
            "is_summary_sensitive",
            "main_sector",
            "priority_level",
            [FieldMapping("priority__code", "priority"), "priority_summary"],
            "product",
            "public_eligibility_summary",
            [
                "sectors",
                "all_sectors",
            ],
            [
                "source",
                "other_source",
            ],
            [
                "status",
                "status_date",
                "status_summary",
                "sub_status",
                "sub_status_other",
            ],
            "summary",
            "term",
            "title",
            "trade_category",
            "trade_direction",
            ["top_priority_status", "top_priority_rejection_summary"],
            "draft",
            # m2m - seperate
            "tags_cache",  # needs cache
            "organisations_cache",  # Needs cache
            "commodities_cache",  # Needs cache
            "categories_cache",  # Needs cache
        )

        if fields is None:
            # TODO: refactor to parametrize fields better
            fields = default_fields

        # Get all fields required - raw changes no enrichment
        return get_model_history(
            qs, model="barrier", fields=fields, track_first_item=track_first_item
        )

    @property
    def latest_progress_update(self):
        if self.progress_updates.all().exists():
            return self.progress_updates.all().latest("created_on")
        return None

    @property
    def latest_programme_fund_progress_update(self):
        if self.programme_fund_progress_updates.exists():
            return self.programme_fund_progress_updates.latest("created_on")
        return None

    @property
    def country_name(self):
        if self.country:
            country = metadata_utils.get_country(str(self.country))
            return country.get("name")

    @property
    def country_trading_bloc(self):
        if self.country:
            return metadata_utils.get_trading_bloc_by_country_id(str(self.country))

    @property
    def location(self):
        return metadata_utils.get_location_text(
            country_id=self.country,
            trading_bloc=self.trading_bloc,
            caused_by_trading_bloc=self.caused_by_trading_bloc,
            admin_area_ids=self.admin_areas,
        )

    def current_progress(self):
        """checks current dataset to see how far reporting workflow is done"""
        progress_list = []
        for stage in REPORT_CONDITIONS:
            stage_code, status = report_stage_status(self, stage)
            progress_list.append((Stage.objects.get(code=stage_code), status))

        return progress_list

    @property
    def current_economic_assessment(self):
        """
        Get the current economic assessment

        Filter in python to avoid another db call if prefetch_related has been used.
        """
        for assessment in self.economic_assessments.all():
            if assessment.approved and not assessment.archived:
                return assessment

    @property
    def current_valuation_assessment(self):
        """
        Get the current valuration assessment

        Filter in python to avoid another db call if prefetch_related has been used.
        """
        for assessment in self.valuation_assessments.all():
            if not assessment.archived:
                return assessment

    @property
    def current_resolvability_assessment(self):
        """
        Get the current resolvability assessment

        Filter in python to avoid another db call if prefetch_related has been used.
        """
        for assessment in self.resolvability_assessments.all():
            if assessment.approved and not assessment.archived:
                return assessment

    @property
    def current_strategic_assessment(self):
        """
        Get the current strategic assessment

        Filter in python to avoid another db call if prefetch_related has been used.
        """
        for assessment in self.strategic_assessments.all():
            if assessment.approved and not assessment.archived:
                return assessment

    @property
    def government_organisations(self):
        """Only returns government organisations"""
        return self.organisations.filter(
            organisation_type__in=GOVERNMENT_ORGANISATION_TYPES
        )

    @government_organisations.setter
    def government_organisations(self, queryset):
        """
        Replaces existing government organisations with the items in queryset,
        leaves non government organisations intact.
        """
        non_gov_orgs_qs = self.organisations.exclude(
            organisation_type__in=GOVERNMENT_ORGANISATION_TYPES
        )
        self.organisations.set(non_gov_orgs_qs | queryset)

    def submit_report(self, submitted_by=None):
        """submit a report, convert it into a barrier"""
        for validator in [validators.ReportReadyForSubmitValidator()]:
            validator.set_instance(self)
            validator()

        if not self.status_date:
            self.status_date = timezone.now()

        self.modified_by = submitted_by
        self.reported_on = timezone.now()
        self.draft = False
        self.save()
        self.progress.all().delete()
        return self

    @property
    def archived_user(self):
        return self._cleansed_username(self.archived_by)

    @property
    def unarchived_user(self):
        return self._cleansed_username(self.unarchived_by)

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)

    @property
    def has_public_barrier(self):
        return hasattr(self, "public_barrier")

    @property
    def has_wto_profile(self):
        return hasattr(self, "wto_profile")

    @property
    def is_resolved(self):
        return self.status == BarrierStatus.RESOLVED_IN_FULL

    @property
    def is_top_priority(self):
        return self.top_priority_status in [
            TOP_PRIORITY_BARRIER_STATUS.APPROVED,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
        ]

    @property
    def is_regional_trade_plan(self):
        # has "Regional Trade Plan" in the tags
        return self.tags.filter(title="Regional Trade Plan").exists()

    def last_seen_by(self, user_id):
        try:
            hit = BarrierUserHit.objects.get(user=user_id, barrier=self)
            return hit.last_seen
        except BarrierUserHit.DoesNotExist:
            return None

    def archive(self, user, reason="", explanation=""):
        try:
            if self.public_barrier.public_view_status == PublicBarrierStatus.PUBLISHED:
                raise ArchivingException("Public barrier should be unpublished first.")
        except PublicBarrier.DoesNotExist:
            pass
        self.archived_explanation = explanation
        self.unarchived_by = None
        self.unarchived_on = None
        self.unarchived_reason = ""
        super().archive(user, reason)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        """
        Upon creating new item, generate a readable reference code
        """
        if self.code is None:
            loop_num = 0
            unique = False
            while not unique:
                if loop_num < settings.REF_CODE_MAX_TRIES:
                    new_code = random_barrier_reference()
                    if not Barrier.objects.filter(code=new_code):
                        self.code = new_code
                        unique = True
                    loop_num += 1
                else:
                    raise ValueError("Error generating a unique reference code.")

        if self.source != BARRIER_SOURCE.OTHER:
            self.other_source = ""

        if self.caused_by_trading_bloc is not None and not self.country_trading_bloc:
            self.caused_by_trading_bloc = None

        super().save(force_insert, force_update, using, update_fields)

        # Ensure that a PublicBarrier for this Barrier exists
        PublicBarrier.public_barriers.get_or_create_for_barrier(barrier=self)


class PublicBarrierHistoricalModel(models.Model):
    """
    Abstract model for tracking m2m changes for PublicBarrier.
    """

    categories_cache = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=list,
    )

    light_touch_reviews_cache = models.JSONField(default=dict)

    def get_changed_fields(self, old_history):  # noqa: C901, E261
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if set(self.categories_cache or []) != set(old_history.categories_cache or []):
            changed_fields.add("categories")

        if (self.light_touch_reviews_cache or {}) != (
            old_history.light_touch_reviews_cache or {}
        ):
            changed_fields.add("light_touch_reviews")

        if "all_sectors" in changed_fields:
            changed_fields.discard("all_sectors")
            changed_fields.add("sectors")

        if "country" in changed_fields:
            changed_fields.discard("country")
            changed_fields.add("location")

        if "trading_bloc" in changed_fields:
            changed_fields.discard("trading_bloc")
            changed_fields.add("location")

        if "caused_by_trading_bloc" in changed_fields:
            if self.caused_by_trading_bloc or old_history.caused_by_trading_bloc:
                changed_fields.add("location")

        if "_title" in changed_fields:
            changed_fields.discard("_title")
            changed_fields.add("title")

        if "_summary" in changed_fields:
            changed_fields.discard("_summary")
            changed_fields.add("summary")

        if "_public_view_status" in changed_fields:
            changed_fields.discard("_public_view_status")
            changed_fields.add("public_view_status")

        return list(changed_fields)

    def update_categories(self):
        self.categories_cache = list(
            self.instance.categories.values_list("id", flat=True)
        )

    def update_light_touch_reviews(self):
        try:
            light_touch_reviews: PublicBarrierLightTouchReviews = (
                self.instance.light_touch_reviews
            )
        except PublicBarrier.light_touch_reviews.RelatedObjectDoesNotExist:
            light_touch_reviews = PublicBarrierLightTouchReviews.objects.create(
                public_barrier=self.instance
            )
        self.light_touch_reviews_cache = {
            "content_team_approval": light_touch_reviews.content_team_approval,
            "has_content_changed_since_approval": light_touch_reviews.has_content_changed_since_approval,
            "hm_trade_commissioner_approval": light_touch_reviews.hm_trade_commissioner_approval,
            "hm_trade_commissioner_approval_enabled": light_touch_reviews.hm_trade_commissioner_approval_enabled,
            "government_organisation_approvals": light_touch_reviews.government_organisation_approvals,
        }

    @property
    def public_view_status(self):
        return self._public_view_status

    @property
    def summary(self):
        return self._summary

    @property
    def title(self):
        return self._title

    def save(self, *args, **kwargs):
        self.update_categories()
        self.update_light_touch_reviews()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class PublicBarrierLightTouchReviews(FullyArchivableMixin, BaseModel):
    public_barrier = models.OneToOneField(
        "PublicBarrier", related_name="light_touch_reviews", on_delete=models.CASCADE
    )

    content_team_approval = models.BooleanField(default=False, blank=True)
    has_content_changed_since_approval = models.BooleanField(default=False, blank=True)
    hm_trade_commissioner_approval = models.BooleanField(default=False, blank=True)
    hm_trade_commissioner_approval_enabled = models.BooleanField(
        default=True, blank=True
    )
    government_organisation_approvals = ArrayField(
        models.IntegerField(blank=True), blank=True, null=False, default=list
    )
    missing_government_organisation_approvals = ArrayField(
        models.IntegerField(blank=True), blank=True, null=False, default=list
    )
    enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        organisation_approval_ids = self.government_organisation_approvals
        all_organisation_ids = (
            self.public_barrier.barrier.organisations.all().values_list("id", flat=True)
        )
        self.missing_government_organisation_approvals = list(
            set(all_organisation_ids) - set(organisation_approval_ids)
        )
        super().save(*args, **kwargs)


class PublicBarrier(FullyArchivableMixin, BaseModel):
    """
    Public barriers are the representation of a barrier (as the name suggests) to the public.
    This table should not be exposed to the public however only to the DMAS frontend which requires login.
    Transfer the data to a flat file or another service which can safely expose the data.
    """

    id = HashidAutoField(
        primary_key=True, min_length=6, alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    barrier = models.OneToOneField(
        Barrier, on_delete=CASCADE, related_name="public_barrier"
    )

    # === Title related fields =====
    _title = models.CharField(blank=True, max_length=MAX_LENGTH)
    title_updated_on = models.DateTimeField(null=True, blank=True)
    internal_title_at_update = models.CharField(blank=True, max_length=MAX_LENGTH)

    # === Summary related fields =====
    _summary = models.TextField(blank=True)
    summary_updated_on = models.DateTimeField(null=True, blank=True)
    internal_summary_at_update = models.TextField(blank=True, max_length=MAX_LENGTH)

    # === Non editable fields ====
    status = models.PositiveIntegerField(choices=BarrierStatus.choices, default=0)
    status_date = models.DateField(blank=True, null=True)
    country = models.UUIDField(blank=True, null=True)
    # caused_by_country_trading_bloc = models.BooleanField(null=True)
    caused_by_trading_bloc = models.BooleanField(blank=True, null=True)
    trading_bloc = models.CharField(
        choices=TRADING_BLOC_CHOICES,
        max_length=7,
        blank=True,
    )
    sectors = ArrayField(models.UUIDField(), blank=True, null=False, default=list)
    all_sectors = models.BooleanField(blank=True, null=True)
    categories = models.ManyToManyField(
        metadata_models.Category, related_name="public_barriers"
    )

    published_versions = models.JSONField(default=dict)

    # === Status and timestamps ====
    _public_view_status = models.PositiveIntegerField(
        choices=PublicBarrierStatus.choices, default=0
    )
    first_published_on = models.DateTimeField(null=True, blank=True)
    last_published_on = models.DateTimeField(null=True, blank=True)
    unpublished_on = models.DateTimeField(null=True, blank=True)

    changed_since_published = models.BooleanField(default=False)

    public_barriers = PublicBarrierManager

    class Meta:
        permissions = [
            ("publish_barrier", "Can publish barrier"),
            (
                "mark_barrier_as_ready_for_publishing",
                "Can mark barrier as ready for publishing",
            ),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # ensure public barrier has light touch reviews
        (
            light_touch_reviews,
            created,
        ) = PublicBarrierLightTouchReviews.objects.get_or_create(public_barrier=self)
        if not light_touch_reviews.enabled:
            if self._title and self._summary:
                light_touch_reviews.enabled = True
                light_touch_reviews.save()

    def add_new_version(self):
        latest_version = self.published_versions.get("latest_version", "0")
        new_version = str(int(latest_version) + 1)
        entry = {
            "version": new_version,
            "published_on": self.last_published_on.isoformat(),
        }
        if not self.published_versions:
            self.published_versions = {"latest_version": "0", "versions": {}}
        self.published_versions["latest_version"] = new_version
        self.published_versions["versions"].setdefault(new_version, entry)

    def get_published_version(self, version):
        version = str(version)
        if self.published_versions:
            timestamp = self.published_versions["versions"][version]["published_on"]
            historic_public_barrier = self.history.as_of(
                datetime.datetime.fromisoformat(timestamp)
            )
            return historic_public_barrier
        else:
            return None

    @property
    def latest_published_version(self):
        return self.get_published_version(
            self.published_versions.get("latest_version", 0)
        )

    def update_non_editable_fields(self):
        self.status = self.internal_status
        self.status_date = self.internal_status_date
        self.country = self.internal_country
        self.caused_by_trading_bloc = self.internal_caused_by_trading_bloc
        self.trading_bloc = self.internal_trading_bloc
        self.sectors = self.internal_sectors
        self.all_sectors = self.internal_all_sectors
        self.categories.set(self.internal_categories.all())

    def publish(self):
        if self.ready_to_be_published:
            self.update_non_editable_fields()
            self.unpublished_on = None
            self.public_view_status = PublicBarrierStatus.PUBLISHED
            self.add_new_version()
            self._history_date = self.last_published_on
            self.save()
            return True
        else:
            return False

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.internal_title_at_update = self.barrier.title
        self.title_updated_on = timezone.now()

    @property
    def title_changed(self):
        if self.title:
            if self.latest_published_version:
                return self.title != self.latest_published_version.title
            else:
                return True
        else:
            return False

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value
        self.internal_summary_at_update = self.barrier.summary
        self.summary_updated_on = timezone.now()

    @property
    def summary_changed(self):
        if self.summary:
            if self.latest_published_version:
                return self.summary != self.latest_published_version.summary
            else:
                return True
        else:
            return False

    @property
    def location(self):
        return metadata_utils.get_location_text(
            country_id=self.country,
            trading_bloc=self.trading_bloc,
            caused_by_trading_bloc=self.caused_by_trading_bloc,
        )

    @property
    def public_view_status(self):
        _old_public_view_status = self._public_view_status

        # set default if eligibility is avail on the internal barrier
        if self._public_view_status == PublicBarrierStatus.UNKNOWN:
            if self.barrier.public_eligibility_postponed is True:
                self._public_view_status = PublicBarrierStatus.REVIEW_LATER
            elif self.barrier.public_eligibility is True:
                self._public_view_status = PublicBarrierStatus.ELIGIBLE
            elif self.barrier.public_eligibility is False:
                self._public_view_status = PublicBarrierStatus.INELIGIBLE

        # The internal barrier might get withdrawn from the public domain
        # in which case it will be marked as ineligible for public view
        # and the public barrier view status should update as well
        #
        # Note: cannot automatically change from published
        #       the public barrier would need to be unpublished first
        if self._public_view_status != PublicBarrierStatus.PUBLISHED:
            if self.barrier.public_eligibility_postponed is True:
                self._public_view_status = PublicBarrierStatus.REVIEW_LATER

            # Marking the public barrier ineligible
            elif self.barrier.public_eligibility is False:
                self._public_view_status = PublicBarrierStatus.INELIGIBLE

            # Marking the public barrier eligible
            elif (
                self.barrier.public_eligibility is True
                and self._public_view_status
                in [PublicBarrierStatus.INELIGIBLE, PublicBarrierStatus.REVIEW_LATER]
            ):
                self._public_view_status = PublicBarrierStatus.ELIGIBLE

        if _old_public_view_status != self._public_view_status:
            # only save when the public view status changes
            self.save()
        return self._public_view_status

    @public_view_status.setter
    def public_view_status(self, value):
        """Set relevant date automatically"""
        status = int(value)
        self._public_view_status = status
        # auto update date fields based on the new status
        now = timezone.now()
        if status == PublicBarrierStatus.PUBLISHED:
            self.first_published_on = self.first_published_on or now
            self.last_published_on = now
        if status == PublicBarrierStatus.UNPUBLISHED:
            self.unpublished_on = now

    @property
    def is_currently_published(self):
        """
        Is this barrier currently visible on the public frontend?
        """
        return self.first_published_on and not self.unpublished_on

    @property
    def internal_title_changed(self):
        if self.internal_title_at_update:
            return self.barrier.title != self.internal_title_at_update
        else:
            return False

    @property
    def internal_summary_changed(self):
        if self.internal_summary_at_update:
            return self.barrier.summary != self.internal_summary_at_update
        else:
            return False

    @property
    def internal_status(self):
        return self.barrier.status

    @property
    def internal_status_changed(self):
        return self.barrier.status != self.status

    @property
    def internal_status_date(self):
        return self.barrier.status_date

    @property
    def internal_status_date_changed(self):
        # Change in status date is only relevant if the barrier is resolved
        return (self.internal_is_resolved or self.is_resolved) and (
            self.internal_status_date != self.status_date
        )

    @property
    def is_resolved(self):
        return self.status == BarrierStatus.RESOLVED_IN_FULL

    @property
    def internal_is_resolved(self):
        return self.barrier.is_resolved

    @property
    def internal_is_resolved_changed(self):
        return self.barrier.is_resolved != self.is_resolved

    @property
    def internal_country(self):
        return self.barrier.country

    @property
    def internal_country_changed(self):
        return self.barrier.country != self.country

    @property
    def internal_caused_by_trading_bloc(self):
        return self.barrier.caused_by_trading_bloc

    @property
    def internal_caused_by_trading_bloc_changed(self):
        return self.barrier.caused_by_trading_bloc != self.caused_by_trading_bloc

    @property
    def internal_trading_bloc(self):
        return self.barrier.trading_bloc

    @property
    def internal_trading_bloc_changed(self):
        return self.barrier.trading_bloc != self.trading_bloc

    @property
    def internal_location(self):
        return metadata_utils.get_location_text(
            country_id=self.barrier.country,
            trading_bloc=self.barrier.trading_bloc,
            caused_by_trading_bloc=self.barrier.caused_by_trading_bloc,
        )

    @property
    def internal_location_changed(self):
        return self.internal_location != self.location

    @property
    def internal_sectors(self):
        return self.barrier.sectors

    @property
    def internal_sectors_changed(self):
        return self.barrier.sectors != self.sectors

    @property
    def internal_main_sector_changed(self):
        return self.barrier.main_sector != self.internal_main_sector

    @property
    def internal_all_sectors(self):
        return self.barrier.all_sectors

    @property
    def internal_main_sector(self):
        return self.barrier.main_sector

    @property
    def internal_all_sectors_changed(self):
        return self.barrier.all_sectors != self.all_sectors

    @property
    def internal_categories(self):
        return self.barrier.categories

    @property
    def internal_categories_changed(self):
        # TODO: consider other options
        return set(self.barrier.categories.all()) != set(self.categories.all())

    @property
    def internal_created_on(self):
        return self.barrier.created_on

    @property
    def ready_to_be_published(self):
        is_ready = self.public_view_status == PublicBarrierStatus.READY
        is_republish = self.unpublished_on is not None
        has_changes = self.unpublished_changes
        has_title_and_summary = bool(self.title and self.summary)
        return is_ready and has_title_and_summary and (is_republish or has_changes)

    @property
    def unpublished_changes(self):
        return (
            self.title_changed
            or self.summary_changed
            or self.internal_title_changed
            or self.internal_summary_changed
            or self.internal_is_resolved_changed
            or self.internal_status_date_changed
            or self.internal_location_changed
            or self.internal_sectors_changed
            or self.internal_main_sector_changed
            or self.internal_all_sectors_changed
            or self.internal_categories_changed
        )

    history = HistoricalRecords(bases=[PublicBarrierHistoricalModel])

    @classmethod
    def get_history(cls, barrier_id):

        qs = cls.history.filter(barrier__id=barrier_id)

        fields = (
            [
                "country",
                "trading_bloc",
                "caused_by_trading_bloc",
            ],
            [
                "sectors",
                "all_sectors",
            ],
            [
                "status",
                "status_date",
            ],
            "_title",
            "_summary",
            "_public_view_status",
            "categories_cache",
        )

        # Get all fields required - raw changes no enrichment
        return get_model_history(qs, model="public_barrier", fields=fields)


class BarrierUserHit(models.Model):
    """Record when a user has most recently seen a barrier."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "barrier"]


class BarrierReportStage(BaseModel):
    """Many to Many between report and workflow stage"""

    barrier = models.ForeignKey(
        Barrier, related_name="progress", on_delete=models.CASCADE
    )
    stage = models.ForeignKey(Stage, related_name="progress", on_delete=models.CASCADE)
    status = models.PositiveIntegerField(choices=STAGE_STATUS, blank=True, null=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = (("barrier", "stage"),)


class BarrierCommodity(models.Model):
    barrier = models.ForeignKey(
        Barrier, related_name="barrier_commodities", on_delete=models.CASCADE
    )
    commodity = models.ForeignKey(
        Commodity, related_name="barrier_commodities", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=10)
    country = models.UUIDField(blank=True, null=True)
    trading_bloc = models.CharField(
        choices=TRADING_BLOC_CHOICES, max_length=7, blank=True
    )
    created_on = models.DateTimeField(auto_now_add=True)

    @property
    def formatted_code(self):
        return format_commodity_code(self.code)

    @property
    def simple_formatted_code(self):
        return format_commodity_code(self.code, separator="")


class BarrierFilterSet(django_filters.FilterSet):
    """
    Custom FilterSet to handle all necessary filters on Barriers
    reported_on_before: filter start date dd-mm-yyyy
    reported_on_after: filter end date dd-mm-yyyy
    cateogory: int, one or more comma seperated category ids
        ex: category=1 or category=1,2
    sector: uuid, one or more comma seperated sector UUIDs
        ex:
        sector=af959812-6095-e211-a939-e4115bead28a
        sector=af959812-6095-e211-a939-e4115bead28a,9538cecc-5f95-e211-a939-e4115bead28a
    status: int, one or more status id's.
        ex: status=1 or status=1,2
    location: UUID, one or more comma seperated overseas region/country/state UUIDs
        ex:
        location=a25f66a0-5d95-e211-a939-e4115bead28a
        location=a25f66a0-5d95-e211-a939-e4115bead28a,955f66a0-5d95-e211-a939-e4115bead28a
    priority: priority code, one or more comma seperated priority codes
        ex: priority=UNKNOWN or priority=UNKNOWN,LOW
    text: combination custom search across multiple fields.
        Searches for reference code,
        barrier title, company names, export description and barrier summary
    """

    reported_on = django_filters.DateFromToRangeFilter("reported_on")
    ignore_all_sectors = django_filters.Filter(method="ignore_all_sectors_filter")
    sector = django_filters.BaseInFilter(method="sector_filter")
    status = django_filters.BaseInFilter("status")
    status_date_open_pending_action = django_filters.Filter(
        method="resolved_date_filter"
    )
    status_date_open_in_progress = django_filters.Filter(method="resolved_date_filter")
    status_date_resolved_in_part = django_filters.Filter(method="resolved_date_filter")
    status_date_resolved_in_full = django_filters.Filter(method="resolved_date_filter")
    delivery_confidence = django_filters.BaseInFilter(method="progress_status_filter")
    category = django_filters.BaseInFilter("categories", distinct=True)
    top_priority = django_filters.BaseInFilter(method="tags_filter")
    priority = django_filters.BaseInFilter(method="priority_filter")
    top_priority_status = django_filters.BaseInFilter(
        method="top_priority_status_filter"
    )
    priority_level = django_filters.BaseInFilter(method="priority_level_filter")
    combined_priority = django_filters.BaseInFilter(method="combined_priority_filter")
    location = django_filters.BaseInFilter(method="location_filter")
    admin_areas = django_filters.BaseInFilter(method="admin_areas_filter")
    search = django_filters.Filter(method="text_search")
    text = django_filters.Filter(method="text_search")

    user = django_filters.Filter(method="my_barriers")
    has_action_plan = django_filters.Filter(method="has_action_plan_filter")

    team = django_filters.Filter(method="team_barriers")
    member = django_filters.Filter(method="member_filter")
    archived = django_filters.BooleanFilter("archived", widget=BooleanWidget)
    economic_assessment_eligibility = django_filters.BaseInFilter(
        method="economic_assessment_eligibility_filter"
    )
    economic_assessment = django_filters.BaseInFilter(
        method="economic_assessment_filter"
    )
    economic_impact_assessment = django_filters.BaseInFilter(
        method="economic_impact_assessment_filter"
    )
    public_view = django_filters.BaseInFilter(method="public_view_filter")
    tags = django_filters.BaseInFilter(method="tags_filter")
    trade_direction = django_filters.BaseInFilter("trade_direction")
    wto = django_filters.BaseInFilter(method="wto_filter")
    organisation = django_filters.BaseInFilter("organisations", distinct=True)
    commodity_code = django_filters.BaseInFilter(method="commodity_code_filter")
    commercial_value_estimate = django_filters.BaseInFilter(
        method="commercial_value_estimate_filter"
    )
    export_types = django_filters.BaseInFilter(method="export_types_filter")
    start_date = django_filters.Filter(method="start_date_filter")

    class Meta:
        model = Barrier
        fields = [
            "country",
            "category",
            "sector",
            "reported_on",
            "status",
            "status_date",
            "priority",
            "archived",
        ]

    def __init__(self, *args, **kwargs):
        if kwargs.get("user"):
            self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def get_user(self):
        if hasattr(self, "user"):
            return self.user
        if self.request is not None:
            return self.request.user

    def sector_filter(self, queryset, name, value: List[str]):
        """
        custom filter for multi-select filtering of Sectors field,
        which is ArrayField
        """

        only_main_sector = self.data.get("only_main_sector", False)

        if only_main_sector:
            if not value:
                return queryset.filter(main_sector__isnull=False)
            else:
                # We're ensuring that main_sector is one of the values provided.
                return queryset.filter(main_sector__in=value)

        # Add overlap condition for sectors if specific sectors are provided
        if value:
            return queryset.filter(
                Q(all_sectors=True)
                | Q(main_sector__in=value)
                | Q(sectors__overlap=value)
            )

        return queryset

    def ignore_all_sectors_filter(self, queryset, name, value):
        """
        ignore all barriers that have 'all sectors' as the sector
        """
        if not value:
            return queryset
        return queryset.exclude(all_sectors=True)

    def top_priority_status_filter(self, queryset, name, value):
        if value:
            # If user is searching for APPROVED top priority barriers, the search must also
            # include barriers PENDING REMOVAL. So if APPROVED is selected, but PENDING
            # REMOVAL has not, we need to include it in the search parameter.
            if "APPROVED" in value and "REMOVAL_PENDING" not in value:
                value.append("REMOVAL_PENDING")

            queryset = queryset.filter(top_priority_status__in=value)
        return queryset

    def priority_level_filter(self, queryset, name, value):
        if value:
            queryset = queryset.filter(priority_level__in=value)
            if "NONE" in value:
                queryset = queryset.filter(
                    (Q(top_priority_status="NONE") & Q(priority_level="NONE"))
                    | Q(priority_level__in=value)
                )
        return queryset

    def priority_filter(self, queryset, name, value):
        """
        customer filter for multi-select of priorities field
        by code rather than priority id.
        UNKNOWN would either mean, UNKNOWN is set in the field
        or priority is not yet set for that barrier
        """
        UNKNOWN = "UNKNOWN"
        priorities = metadata_models.BarrierPriority.objects.filter(code__in=value)

        if UNKNOWN in value:
            return queryset.filter(
                Q(priority__isnull=True) | Q(priority__in=priorities)
            )
        else:
            return queryset.filter(priority__in=priorities)

    def combined_priority_filter(self, queryset, name, value):
        """
        customer filter for multi-select of Barrier Priority and Top 100
        filters
        """

        if value:
            # If user is searching for APPROVED top priority barriers, the search must also
            # include barriers PENDING REMOVAL. So if APPROVED is selected, but PENDING
            # REMOVAL has not, we need to include it in the search parameter.
            if "APPROVED" in value and "REMOVAL_PENDING" not in value:
                value.append("REMOVAL_PENDING")

            if "NONE" in value:
                if len(value) > 1:
                    # We have additional filters so need to combine with NONE query
                    value.remove("NONE")
                    queryset = queryset.filter(
                        Q(top_priority_status__in=value)
                        | Q(priority_level__in=value)
                        | (Q(top_priority_status="NONE") & Q(priority_level="NONE")),
                    )
                else:
                    queryset = queryset.filter(
                        (Q(top_priority_status="NONE") & Q(priority_level="NONE")),
                    )
            else:
                queryset = queryset.filter(
                    Q(top_priority_status__in=value) | Q(priority_level__in=value)
                )

        return queryset

    def progress_status_filter(self, queryset, name, value):
        # First query to run will filter out each unique Barriers historical updates, leaving the latest entries
        # the query wrapping it will cut out all the progress_status's that don't match the search query
        delivery_confidences = BarrierProgressUpdate.objects.filter(
            id__in=BarrierProgressUpdate.objects.distinct("barrier_id")
            .order_by("-barrier_id", "-created_on")
            .values("id")
        ).filter(status__in=value)

        return queryset.filter(progress_updates__in=delivery_confidences)

    def has_action_plan_filter(self, queryset, name, value):
        if not value:
            return queryset

        from api.action_plans.models import ActionPlan

        active_action_plans = ActionPlan.objects.get_active_action_plans().all()

        return queryset.filter(action_plan__in=active_action_plans)

    def clean_location_value(self, value):  # noqa: C901
        """
        Splits a list of locations into countries, regions and trading blocs
        """
        location_values = []
        overseas_region_values = []
        trading_bloc_values = []
        overseas_region_countries = []

        for location in value:
            if location in TRADING_BLOCS:
                trading_bloc_values.append(location)
            else:
                location_values.append(location)

        # Add all countries within the overseas regions
        for country in cache.get_or_set(
            "dh_countries", metadata_utils.get_countries, 72000
        ):
            if (
                country["overseas_region"]
                and country["overseas_region"]["id"] in location_values
            ):
                overseas_region_countries.append(country["id"])
                if country["overseas_region"]["id"] not in overseas_region_values:
                    overseas_region_values.append(country["overseas_region"]["id"])

            # For custom overseas region "Wider Europe" we need to build a seperate list
            # If the country is in the wider europe constant, we want it displayed
            if "wider_europe" in value and country["name"] in WIDER_EUROPE_REGIONS:
                overseas_region_countries.append(country["id"])

        # Add all trading blocs associated with the overseas regions
        for overseas_region in overseas_region_values:
            for trading_bloc in TRADING_BLOCS.values():
                if overseas_region in trading_bloc["overseas_regions"]:
                    trading_bloc_values.append(trading_bloc["code"])

        # Need to remove "wider_europe" from location_values as it isn't a searchable UUID
        if "wider_europe" in location_values:
            location_values.remove("wider_europe")

        # Return cleaned value arrays
        return {
            "countries": [
                location
                for location in location_values
                if location not in overseas_region_values
            ],
            "overseas_regions": overseas_region_values,
            "overseas_region_countries": overseas_region_countries,
            "trading_blocs": trading_bloc_values,
        }

    def location_filter(self, queryset, name, value):
        """
        custom filter for retrieving barriers of all countries of an overseas region
        """
        location = self.clean_location_value(value)

        tb_queryset = queryset.none()

        if location["trading_blocs"]:
            tb_queryset = queryset.filter(trading_bloc__in=location["trading_blocs"])

            if "country_trading_bloc" in self.data:
                trading_bloc_countries = []
                for trading_bloc in self.data["country_trading_bloc"].split(","):
                    trading_bloc_countries += (
                        metadata_utils.get_trading_bloc_country_ids(trading_bloc)
                    )

                tb_queryset = tb_queryset | queryset.filter(
                    country__in=trading_bloc_countries,
                    caused_by_trading_bloc=True,
                )

        return tb_queryset | queryset.filter(
            Q(country__in=location["countries"])
            | Q(country__in=location["overseas_region_countries"])
            | Q(admin_areas__overlap=location["countries"])
        )

    def admin_areas_filter(self, queryset, name, value):
        """
        Custom filter to filter by a country's administrative areas (states/provinces)
        """
        # Since we are comparing 2 lists we need to use reduce to allow the for loop
        # to go through each submitted admin_area id and append a Q object seperated
        # by an OR operator | to the query which will check the individual selected value
        # is present in the list of admin_areas stored on the barrier
        return queryset.filter(
            reduce(
                operator.or_,
                (Q(admin_areas__contains=[selected_area]) for selected_area in value),
            )
        )

    def text_search(self, queryset, name, value):
        """
        custom text search against multiple fields
            full value of code
            full text search on summary
            partial search on title
        """

        MAX_DEPTH_COUNT = 20

        # Assuming the name field can appear in any of the nested dicts inside companies/related_organisations
        company_queries = []
        for i in range(MAX_DEPTH_COUNT):
            company_queries.append(Q(**{f"companies__{i}__name__icontains": value}))
            company_queries.append(
                Q(**{f"related_organisations__{i}__name__icontains": value})
            )

        combined_company_related_organisation_query = Q()
        for query in company_queries:
            combined_company_related_organisation_query |= query

        return queryset.annotate(
            search=SearchVector("summary", "export_description"),
        ).filter(
            Q(code__icontains=value)
            | Q(search=value)
            | Q(title__icontains=value)
            | Q(public_barrier__id__iexact=value.lstrip("PID-").upper())
            | Q(combined_company_related_organisation_query)
        )

    def my_barriers(self, queryset, name, value):
        if value:
            current_user = self.get_user()
            qs = queryset.filter(created_by=current_user, draft=False)
            return qs
        return queryset

    def team_barriers(self, queryset, name, value):
        if value:
            current_user = self.get_user()
            return queryset.filter(
                Q(barrier_team__user=current_user) & Q(barrier_team__archived=False)
            ).exclude(created_by=current_user)
        return queryset

    def member_filter(self, queryset, name, value):
        if value:
            member = get_object_or_404(collaboration_models.TeamMember, pk=value)
            return queryset.filter(barrier_team__user=member.user)
        return queryset

    def public_view_filter(self, queryset, name, value):
        public_queryset = queryset.none()

        if "changed" in value:
            value.remove("changed")
            public_queryset = queryset.filter(
                public_barrier__changed_since_published=True
            )

        if "not_yet_sifted" in value:
            value.remove("not_yet_sifted")
            public_queryset = queryset.filter(public_eligibility=None)

        status_lookup = {
            "unknown": PublicBarrierStatus.UNKNOWN,
            "ineligible": PublicBarrierStatus.INELIGIBLE,
            "eligible": PublicBarrierStatus.ELIGIBLE,
            "ready": PublicBarrierStatus.READY,
            "published": PublicBarrierStatus.PUBLISHED,
            "unpublished": PublicBarrierStatus.UNPUBLISHED,
            "review_later": PublicBarrierStatus.REVIEW_LATER,
        }
        statuses = [
            status_lookup.get(status)
            for status in value
            if status in status_lookup.keys()
        ]
        public_queryset = public_queryset | queryset.filter(
            public_barrier___public_view_status__in=statuses
        )
        return queryset & public_queryset

    def tags_filter(self, queryset, name, value):
        return queryset.filter(tags__in=value)

    def resolved_date_filter(self, queryset, name, value):
        dates_list = value.split(",")
        start_date = dates_list[0]
        end_date = dates_list[1]

        # Exlude any barrier from the result which has the corresponding status but sits outside
        # the given range.
        if name == "status_date_resolved_in_full":
            return queryset.exclude(
                Q(status__in="4"), ~Q(status_date__range=(start_date, end_date))
            )
        elif name == "status_date_resolved_in_part":
            return queryset.exclude(
                Q(status__in="3"),
                ~Q(status_date__range=(start_date, end_date)),
            )
        elif name == "status_date_open_in_progress":
            return queryset.exclude(
                Q(status__in="2"),
                ~Q(estimated_resolution_date__range=(start_date, end_date)),
            )
        elif name == "status_date_open_pending_action":
            return queryset.exclude(
                Q(status__in="1"),
                ~Q(estimated_resolution_date__range=(start_date, end_date)),
            )

    def wto_filter(self, queryset, name, value):
        wto_queryset = queryset.none()

        if "wto_has_been_notified" in value:
            wto_queryset = wto_queryset | queryset.filter(
                wto_profile__wto_has_been_notified=True
            )
        if "wto_should_be_notified" in value:
            wto_queryset = wto_queryset | queryset.filter(
                wto_profile__wto_should_be_notified=True
            )
        if "has_raised_date" in value:
            wto_queryset = wto_queryset | queryset.filter(
                wto_profile__raised_date__isnull=False
            )
        if "has_committee_raised_in" in value:
            wto_queryset = wto_queryset | queryset.filter(
                wto_profile__committee_raised_in__isnull=False
            )
        if "has_case_number" in value:
            wto_queryset = wto_queryset | queryset.filter(
                wto_profile__isnull=False
            ).exclude(wto_profile__case_number="")
        if "has_no_information" in value:
            wto_queryset = wto_queryset | queryset.filter(wto_profile__isnull=True)

        return queryset & wto_queryset

    def economic_assessment_eligibility_filter(
        self, queryset: QuerySet, name: str, value: List[str]
    ):
        if not value:
            return queryset

        base_query = queryset.none()

        if "eligible" in value:
            base_query = base_query | queryset.filter(
                economic_assessment_eligibility=True
            )

        if "ineligible" in value:
            base_query = base_query | queryset.filter(
                economic_assessment_eligibility=False
            )

        if "not_yet_marked" in value:
            base_query = base_query | queryset.filter(
                economic_assessment_eligibility__isnull=True
            )

        return base_query

    def economic_assessment_filter(self, queryset, name, value):
        assessment_queryset = queryset.none()

        if "with" in value:
            assessment_queryset = assessment_queryset | queryset.filter(
                economic_assessments__archived=False,
            )
        if "without" in value:
            assessment_queryset = assessment_queryset | queryset.filter(
                economic_assessments__isnull=True,
            )
        if "ready_for_approval" in value:
            assessment_queryset = assessment_queryset | queryset.filter(
                economic_assessments__archived=False,
                economic_assessments__ready_for_approval=True,
                economic_assessments__approved__isnull=True,
            )

        return queryset & assessment_queryset

    def economic_impact_assessment_filter(self, queryset, name, value):
        assessment_queryset = queryset.none()

        if "with" in value:
            assessment_queryset = assessment_queryset | queryset.filter(
                economic_assessments__economic_impact_assessments__archived=False,
            )
        if "without" in value:
            assessment_queryset = assessment_queryset | queryset.filter(
                economic_assessments__economic_impact_assessments__isnull=True,
            )

        return queryset & assessment_queryset

    def commodity_code_filter(self, queryset, name, value):
        filters = Q()
        if "with" in value:
            filters &= ~Q(commodities=None)
        if "without" in value:
            filters &= Q(commodities=None)
        return queryset.filter(filters)

    def commercial_value_estimate_filter(self, queryset, name, value):
        filters = Q()
        if "with" in value:
            filters &= ~Q(commercial_value=None)
        if "without" in value:
            filters &= Q(commercial_value=None)
        return queryset.filter(filters)

    def export_types_filter(self, queryset, name, value: List[str]):
        # Filtering the queryset based on the selected export types
        return queryset.filter(export_types__name__in=value)

    def start_date_filter(self, queryset, name, value):
        dates_list = value.split(",")
        start_date = dates_list[0]
        end_date = dates_list[1]
        # Filtering the queryset based on the start_date range
        return queryset.filter(start_date__range=(start_date, end_date))


class PublicBarrierFilterSet(django_filters.FilterSet):
    """
    Custom FilterSet to handle filters on PublicBarriers
    """

    status = django_filters.BaseInFilter("_public_view_status", method="status_filter")
    country = django_filters.BaseInFilter("country")
    location = django_filters.BaseInFilter(method="location_filter")
    region = django_filters.BaseInFilter(method="region_filter")
    sector = django_filters.BaseInFilter(method="sector_filter")
    organisation = django_filters.BaseInFilter(method="organisation_filter")
    awaiting_review_from = django_filters.BaseInFilter(
        method="awaiting_review_from_filter"
    )

    def sector_filter(self, queryset, name, value):
        """
        custom filter for multi-select filtering of Sectors field,
        which is ArrayField
        """
        return queryset.filter(
            Q(barrier__all_sectors=True) | Q(barrier__sectors__overlap=value)
        )

    def awaiting_review_from_filter(self, queryset, name, value):
        AWAITING_REVIEW_FROM_MAP = AWAITING_REVIEW_FROM._identifier_map
        q_filters = Q()
        if AWAITING_REVIEW_FROM_MAP["CONTENT"] in value:
            q_filters = q_filters | Q(
                light_touch_reviews__enabled=True,
                light_touch_reviews__content_team_approval=False,
            )

        if AWAITING_REVIEW_FROM_MAP["CONTENT_AFTER_CHANGES"] in value:
            q_filters = q_filters | Q(
                light_touch_reviews__enabled=True,
                light_touch_reviews__has_content_changed_since_approval=True,
            )

        if AWAITING_REVIEW_FROM_MAP["HM_TRADE_COMMISSION"] in value:
            q_filters = q_filters | Q(
                light_touch_reviews__enabled=True,
                light_touch_reviews__hm_trade_commissioner_approval=False,
                light_touch_reviews__hm_trade_commissioner_approval_enabled=True,
            )

        if AWAITING_REVIEW_FROM_MAP["GOVERNMENT_ORGANISATION"] in value:
            q_filters = q_filters | Q(
                light_touch_reviews__enabled=True,
                light_touch_reviews__missing_government_organisation_approvals__len__gt=0,
            )

        return queryset.filter(q_filters)

    def organisation_filter(self, queryset, name, value):
        """
        custom filter for multi-select filtering of Government Organisations field,
        which is a ManyToMany on the Barrier model
        """
        return queryset.filter(barrier__organisations__id__in=value)

    def region_filter(self, queryset, name, value):
        countries = set()
        for region_id in value:
            countries.update(
                metadata_utils.get_country_ids_by_overseas_region(region_id)
            )
        return queryset.filter(barrier__country__in=countries)

    def status_filter(self, queryset, name, value):
        """
        Filters on _public_view_status and if value is 'change'
        only select public barriers where the parent barrier had some
        changes
        """
        public_queryset = queryset.none()

        if "changed" in value:
            value.remove("changed")
            public_queryset = queryset.filter(changed_since_published=True)

        if "not_yet_sifted" in value:
            value.remove("not_yet_sifted")
            public_queryset = queryset.filter(public_eligibility=None)

        statuses = [int(status) for status in value]
        public_queryset = public_queryset | queryset.filter(
            _public_view_status__in=statuses
        )
        return queryset & public_queryset

    def location_filter(self, queryset, name, value):
        """
        custom filter for retrieving barriers of all countries of an overseas region
        """
        location = self.clean_location_value(value)

        tb_queryset = queryset.none()

        if location["trading_blocs"]:
            tb_queryset = queryset.filter(
                barrier__trading_bloc__in=location["trading_blocs"]
            )

            if "country_trading_bloc" in self.data:
                trading_bloc_countries = []
                for trading_bloc in self.data["country_trading_bloc"].split(","):
                    trading_bloc_countries += (
                        metadata_utils.get_trading_bloc_country_ids(trading_bloc)
                    )

                tb_queryset = tb_queryset | queryset.filter(
                    barrier__country__in=trading_bloc_countries,
                    barrier__caused_by_trading_bloc=True,
                )

        return tb_queryset | queryset.filter(
            Q(barrier__country__in=location["countries"])
            | Q(barrier__country__in=location["overseas_region_countries"])
            | Q(barrier__admin_areas__overlap=location["countries"])
        )


User = get_user_model()


class BarrierRequestDownloadApproval(models.Model):
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="barrier_request_download_approvals",
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)

    def send_notification(self):
        if self.notification_sent:
            return

        recipient_emails = settings.SEARCH_DOWNLOAD_APPROVAL_REQUEST_EMAILS

        client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
        group_id = Group.objects.get(
            name=settings.APPROVED_FOR_BARRIER_DOWNLOADS_GROUP_NAME
        ).id
        user_group_approval_path = f"/users/add/?group={group_id}"
        approval_url: str = urllib.parse.urljoin(
            settings.FRONTEND_DOMAIN, user_group_approval_path
        )
        for recipient_email in recipient_emails:
            client.send_email_notification(
                email_address=recipient_email,
                template_id=settings.SEARCH_DOWNLOAD_APPROVAL_NOTIFICATION_ID,
                personalisation={
                    "first_name": self.user.first_name.capitalize(),
                    "last_name": self.user.last_name.capitalize(),
                    "administration_link": approval_url,
                    "email_address": self.user.email,
                },
            )

        self.notification_sent = True
        self.notification_sent_at = timezone.now()
        self.save()


class BarrierSearchCSVDownloadEvent(models.Model):
    email = models.EmailField()
    barrier_ids = models.TextField(validators=[int_list_validator])
    created = models.DateTimeField(auto_now_add=True)


class BarrierTopPrioritySummary(models.Model):
    top_priority_summary_text = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="top_priority_summary_submit_user",
    )
    created_on = models.DateTimeField(null=True, blank=True, auto_now=False)
    modified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="top_priority_summary_modify_user",
    )
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=False)
    barrier = models.ForeignKey(
        Barrier,
        blank=True,
        on_delete=models.CASCADE,
        related_name="top_priority_summary",
        primary_key=True,
    )
    history = HistoricalRecords()

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(barrier__id=barrier_id)
        fields = ("top_priority_summary_text",)

        return get_model_history(
            qs,
            model="barrier_top_priority_summary",  # TODO: Update frontend, legacy history marked this as barrier item
            fields=fields,
            track_first_item=True,
        )


class BarrierNextStepItem(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    status = models.CharField(
        max_length=15,
        choices=NEXT_STEPS_ITEMS_STATUS_CHOICES,
        default=NEXT_STEPS_ITEMS_STATUS_CHOICES.IN_PROGRESS,
        blank=True,
    )
    next_step_owner = models.TextField()
    next_step_item = models.TextField()
    start_date = models.DateField(blank=True, null=True, auto_now_add=True)
    completion_date = models.DateField(blank=True, null=True)
    barrier = models.ForeignKey(
        "Barrier",
        blank=True,
        on_delete=models.CASCADE,
        related_name="next_steps_items",
    )
    history = HistoricalRecords()

    class Meta:
        # order by date descending
        ordering = ("-completion_date",)
        verbose_name = "Barrier Next Step Item"
        verbose_name_plural = "Barrier Next Step Items"

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(barrier__id=barrier_id)
        fields = ("status", "next_step_item")

        return get_model_history(
            qs,
            model="barrier",
            fields=fields,
        )
