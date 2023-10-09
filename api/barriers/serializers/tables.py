import datetime
from collections import defaultdict, Counter

from rest_framework import serializers

from api.barriers.models import Barrier
from api.metadata.constants import BarrierStatus
from api.metadata.utils import get_country_to_overseas_region

class BarrierStatusSerializer(serializers.Serializer):
    @property
    def data(self):
        queryset = Barrier.objects.all()
        datasets = defaultdict(list)
        country_to_overseas_regions = get_country_to_overseas_region()
        barrier_statuses = [each[1] for each in BarrierStatus.choices if each[0] not in [BarrierStatus.UNKNOWN, BarrierStatus.OPEN_PENDING, BarrierStatus.UNFINISHED]]
        for barrier in queryset:
            if overseas_region_name := country_to_overseas_regions.get(
                str(barrier.country), {}
            ).get("name"):
                datasets[overseas_region_name].append(barrier.get_status_display())

        counters = {}
        for region, values in datasets.items():
            counters[region] = Counter(values)

        response_data = {
            "graph_data": {
                "labels": barrier_statuses,
                "datasets": [{"label": region, "data": [counters[region].get(status, 0) for status in barrier_statuses]} for region in datasets.keys()]
            },
            "table_data": {
                "columns": [{"title": "Region"}] + [{"title": status} for status in barrier_statuses],
                "rows": [[region] + [counters[region].get(status, 0) for status in barrier_statuses] for region in datasets.keys()]
            }
        }
        return response_data


class UnresolvedBarrierSerializer(serializers.Serializer):
    @property
    def data(self):
        six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
        six_months_ago = six_months_ago.replace(day=1)
        months_in_between = []
        for i in range(6):
            months_in_between.append(six_months_ago)
            six_months_ago = six_months_ago + datetime.timedelta(days=31)
            six_months_ago = six_months_ago.replace(day=1)

        datasets = []
        for status in BarrierStatus.choices:
            label= status[1]
            data = []
            for month in months_in_between:
                barrier_state_count = len([each for each in Barrier.history.as_of(month) if each.status == status[0]])
                data.append(barrier_state_count)

            data.append(Barrier.objects.filter(status=status[0]).count())
            datasets.append({"label": label, "data": data})

        labels = [each.strftime("%-dst %B") for each in months_in_between]
        labels.append("Now")
        return {
            "graph_data": {
                "labels": labels,
                "datasets": datasets
            },
            "table_data": {
                "columns": [{"title": "Month"}] + [{"title": label} for label in labels],
                "rows": [[each["label"]] + each["data"] for each in datasets]
            }
        }
