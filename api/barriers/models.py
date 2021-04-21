import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import CASCADE, Q
from django.utils import timezone
from hashid_field import HashidAutoField
from simple_history.models import HistoricalRecords

from api.barriers import validators
from api.barriers.report_stages import REPORT_CONDITIONS, report_stage_status
from api.barriers.utils import random_barrier_reference
from api.commodities.models import Commodity
from api.commodities.utils import format_commodity_code
from api.core.exceptions import ArchivingException
from api.core.models import BaseModel, FullyArchivableMixin
from api.metadata.constants import (
    BARRIER_ARCHIVED_REASON,
    BARRIER_PENDING,
    BARRIER_SOURCE,
    BARRIER_TERMS,
    GOVERNMENT_ORGANISATION_TYPES,
    STAGE_STATUS,
    TRADE_CATEGORIES,
    TRADE_DIRECTION_CHOICES,
    TRADING_BLOC_CHOICES,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.metadata.models import BarrierPriority, BarrierTag, Category, Organisation
from api.metadata.utils import (
    get_country,
    get_location_text,
    get_trading_bloc_by_country_id,
)

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Stage(models.Model):
    """ Reporting workflow stages  """

    code = models.CharField(max_length=4)
    description = models.CharField(max_length=MAX_LENGTH)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code


class ReportManager(models.Manager):
    """ Manage reports within the model, with draft=True """

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


class Barrier(FullyArchivableMixin, BaseModel):
    """ Barrier Instance, converted from a completed and accepted Report """

    id = models.UUIDField(primary_key=True, default=uuid4)
    code = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        null=True,
        unique=True,
        help_text="Readable reference code e.g. B-20-NTZ",
        db_index=True,
    )
    term = models.PositiveIntegerField(
        choices=BARRIER_TERMS,
        blank=True,
        null=True,
        help_text="Is this a short-term procedural or long-term strategic barrier?",
    )
    end_date = models.DateField(
        blank=True, null=True, help_text="Date the barrier ends"
    )
    country = models.UUIDField(blank=True, null=True)
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
    companies = models.JSONField(blank=True, null=True)
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
    categories = models.ManyToManyField(Category, related_name="barriers")
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
            "otherwise the current time when the status was set."
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

    # Barrier priority
    priority = models.ForeignKey(
        BarrierPriority,
        default=1,
        related_name="barrier",
        on_delete=models.PROTECT,
    )
    priority_summary = models.TextField(blank=True)
    priority_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    stages = models.ManyToManyField(
        Stage,
        related_name="report_stages",
        through="BarrierReportStage",
        help_text="Store reporting stages before submitting",
    )
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
        Organisation, help_text="Organisations that are related to the barrier"
    )

    history = HistoricalRecords(bases=[BarrierHistoricalModel])

    tags = models.ManyToManyField(BarrierTag)

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
        ]

    @property
    def country_name(self):
        if self.country:
            country = get_country(str(self.country))
            return country.get("name")

    @property
    def country_trading_bloc(self):
        if self.country:
            return get_trading_bloc_by_country_id(str(self.country))

    @property
    def location(self):
        return get_location_text(
            country_id=self.country,
            trading_bloc=self.trading_bloc,
            caused_by_trading_bloc=self.caused_by_trading_bloc,
            admin_area_ids=self.admin_areas,
        )

    def current_progress(self):
        """ checks current dataset to see how far reporting workflow is done """
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
        """ Only returns government organisations """
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
        """ submit a report, convert it into a barrier """
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

    def get_changed_fields(self, old_history):
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if set(self.categories_cache or []) != set(old_history.categories_cache or []):
            changed_fields.add("categories")

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
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


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
    categories = models.ManyToManyField(Category, related_name="public_barriers")

    published_versions = models.JSONField(default=dict)

    # === Status and timestamps ====
    _public_view_status = models.PositiveIntegerField(
        choices=PublicBarrierStatus.choices, default=0
    )
    first_published_on = models.DateTimeField(null=True, blank=True)
    last_published_on = models.DateTimeField(null=True, blank=True)
    unpublished_on = models.DateTimeField(null=True, blank=True)

    public_barriers = PublicBarrierManager

    class Meta:
        permissions = [
            ("publish_barrier", "Can publish barrier"),
            (
                "mark_barrier_as_ready_for_publishing",
                "Can mark barrier as ready for publishing",
            ),
        ]

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
        # self.caused_by_country_trading_bloc = self.internal_caused_by_trading_bloc
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
        return get_location_text(
            country_id=self.country,
            trading_bloc=self.trading_bloc,
            caused_by_trading_bloc=self.caused_by_trading_bloc,
        )

    @property
    def public_view_status(self):
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
            if (
                self.barrier.public_eligibility_postponed is True
                and self._public_view_status != PublicBarrierStatus.REVIEW_LATER
            ):
                self._public_view_status = PublicBarrierStatus.REVIEW_LATER
                self.save()

            # Marking the public barrier ineligible
            elif (
                self.barrier.public_eligibility is False
                and self._public_view_status != PublicBarrierStatus.INELIGIBLE
            ):
                self._public_view_status = PublicBarrierStatus.INELIGIBLE
                self.save()

            # Marking the public barrier eligible
            elif (
                self.barrier.public_eligibility is True
                and self._public_view_status in [PublicBarrierStatus.INELIGIBLE, PublicBarrierStatus.REVIEW_LATER]
            ):
                self._public_view_status = PublicBarrierStatus.ELIGIBLE
                self.save()

        return self._public_view_status

    @public_view_status.setter
    def public_view_status(self, value):
        """ Set relevant date automatically """
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
        # return self.barrier.caused_by_trading_bloc != self.caused_by_country_trading_bloc
        return self.barrier.caused_by_trading_bloc != self.caused_by_trading_bloc

    @property
    def internal_trading_bloc(self):
        return self.barrier.trading_bloc

    @property
    def internal_trading_bloc_changed(self):
        return self.barrier.trading_bloc != self.trading_bloc

    @property
    def internal_location(self):
        return get_location_text(
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
    def internal_all_sectors(self):
        return self.barrier.all_sectors

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
            or self.internal_all_sectors_changed
            or self.internal_sectors_changed
            or self.internal_categories_changed
        )

    history = HistoricalRecords(bases=[PublicBarrierHistoricalModel])


class BarrierUserHit(models.Model):
    """Record when a user has most recently seen a barrier."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "barrier"]


class BarrierReportStage(BaseModel):
    """ Many to Many between report and workflow stage """

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
