from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404

import django_filters
from django_filters.widgets import BooleanWidget

from api.barriers.models import BarrierInstance
from api.collaboration.models import TeamMember
from api.metadata.models import BarrierPriority
from api.metadata.utils import get_countries


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
        location=aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc
        location=aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc,955f66a0-5d95-e211-a939-e4115bead28a
    priority: priority code, one or more comma seperated priority codes
        ex: priority=UNKNOWN or priority=UNKNOWN,LOW
    text: combination custom search across multiple fields.
        Searches for reference code,
        barrier title and barrier summary
    """

    reported_on = django_filters.DateFromToRangeFilter("reported_on")
    sector = django_filters.BaseInFilter(method="sector_filter")
    status = django_filters.BaseInFilter("status")
    category = django_filters.BaseInFilter("categories", distinct=True)
    priority = django_filters.BaseInFilter(method="priority_filter")
    location = django_filters.BaseInFilter(method="location_filter")
    search = django_filters.Filter(method="text_search")
    text = django_filters.Filter(method="text_search")
    user = django_filters.Filter(method="my_barriers")
    team = django_filters.Filter(method="team_barriers")
    member = django_filters.Filter(method="member_filter")
    archived = django_filters.BooleanFilter("archived", widget=BooleanWidget)
    tags = django_filters.BaseInFilter(method="tags_filter")
    trade_direction = django_filters.BaseInFilter("trade_direction")
    wto = django_filters.BaseInFilter(method="wto_filter")

    class Meta:
        model = BarrierInstance
        fields = [
            "export_country",
            "category",
            "sector",
            "reported_on",
            "status",
            "priority",
            "archived",
        ]

    def __init__(self, *args, **kwargs):
        if kwargs.get("user"):
            self.user = kwargs.pop("user")
        return super().__init__(*args, **kwargs)

    def get_user(self):
        if hasattr(self, "user"):
            return self.user
        if self.request is not None:
            return self.request.user

    def sector_filter(self, queryset, name, value):
        """
        custom filter for multi-select filtering of Sectors field,
        which is ArrayField
        """
        return queryset.filter(
            Q(all_sectors=True) | Q(sectors__overlap=value)
        )

    def priority_filter(self, queryset, name, value):
        """
        customer filter for multi-select of priorities field
        by code rather than priority id.
        UNKNOWN would either mean, UNKNOWN is set in the field
        or priority is not yet set for that barrier
        """
        UNKNOWN = "UNKNOWN"
        priorities = BarrierPriority.objects.filter(code__in=value)
        if UNKNOWN in value:
            return queryset.filter(
                Q(priority__isnull=True) | Q(priority__in=priorities)
            )
        else:
            return queryset.filter(priority__in=priorities)

    def location_filter(self, queryset, name, value):
        """
        custom filter for retreiving barriers of all countries of an overseas region
        """
        countries = cache.get_or_set("dh_countries", get_countries, 72000)
        countries_for_region = [
            item["id"]
            for item in countries
            if item["overseas_region"] and item["overseas_region"]["id"] in value
        ]
        return queryset.filter(
            Q(export_country__in=value) |
            Q(export_country__in=countries_for_region) |
            Q(country_admin_areas__overlap=value)
        )

    def text_search(self, queryset, name, value):
        """
        custom text search against multiple fields
            full value of code
            full text search on summary
            partial search on barrier_title
        """
        return queryset.annotate(
            search=SearchVector('summary')
        ).filter(
            Q(code=value) | Q(search=value) | Q(barrier_title__icontains=value)
        )

    def my_barriers(self, queryset, name, value):
        if value:
            current_user = self.get_user()
            qs = queryset.filter(created_by=current_user)
            return qs
        return queryset

    def team_barriers(self, queryset, name, value):
        if value:
            current_user = self.get_user()
            return queryset.filter(
                Q(barrier_team__user=current_user) & Q(barrier_team__archived=False)
            ).distinct()
        return queryset

    def member_filter(self, queryset, name, value):
        if value:
            member = get_object_or_404(TeamMember, pk=value)
            return queryset.filter(barrier_team__user=member.user).distinct()
        return queryset

    def tags_filter(self, queryset, name, value):
        return queryset.filter(tags__in=value).distinct()

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
