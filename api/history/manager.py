import datetime

from api.history.models import CachedHistoryItem

from .factories import (
    AssessmentHistoryFactory,
    BarrierHistoryFactory,
    NoteHistoryFactory,
    PublicBarrierNoteHistoryFactory,
    PublicBarrierHistoryFactory,
    TeamMemberHistoryFactory,
    WTOHistoryFactory,
)


class HistoryManager:
    """
    Used for querying history items.

    Can either query the cache or generate history items from scratch.
    """

    @classmethod
    def get_activity(cls, barrier, use_cache=False):
        barrier_history = cls.get_barrier_history(
            barrier_id=barrier.pk,
            fields=["archived", "priority", "status"],
            use_cache=use_cache,
        )
        assessment_history = cls.get_assessment_history(
            barrier_id=barrier.pk,
            fields=[
                "commercial_value",
                "export_value",
                "impact",
                "import_market_size",
                "value_to_economy",
            ],
            use_cache=use_cache,
        )
        return barrier_history + assessment_history

    @classmethod
    def get_full_history(cls, barrier, use_cache=False):
        if use_cache:
            cached_history_items = CachedHistoryItem.objects.filter(
                barrier_id=barrier.pk,
                date__gt=barrier.reported_on + datetime.timedelta(seconds=1),
            )
            history_items = []
            for item in cached_history_items:
                history_item = item.as_history_item()
                if history_item.is_valid():
                    history_items.append(item.as_history_item())
            return history_items

        barrier_history = cls.get_barrier_history(barrier.pk, start_date=barrier.reported_on)
        notes_history = cls.get_notes_history(barrier.pk, start_date=barrier.reported_on)
        assessment_history = cls.get_assessment_history(barrier.pk, start_date=barrier.reported_on)
        team_history = cls.get_team_history(
            barrier.pk,
            start_date=barrier.reported_on + datetime.timedelta(seconds=1)
        )
        wto_history = cls.get_wto_history(barrier.pk, start_date=barrier.reported_on)

        history_items = (
            barrier_history + notes_history + assessment_history + team_history
            + wto_history
        )

        if hasattr(barrier, "public_barrier"):
            history_items += cls.get_public_barrier_history(
                barrier.pk,
                start_date=barrier.public_barrier.created_on + datetime.timedelta(seconds=1)
            )
            history_items += cls.get_public_barrier_notes_history(barrier.pk)

        return history_items

    @classmethod
    def get_cached_history_items(cls, barrier_id, model, fields=(), start_date=None):
        queryset = CachedHistoryItem.objects.filter(
            barrier_id=barrier_id,
            model=model,
        )
        if start_date:
            queryset = queryset.filter(date__gt=start_date)
        if fields:
            queryset = queryset.filter(field__in=fields)
        return [item.as_history_item() for item in queryset]

    @classmethod
    def get_assessment_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="assessment",
                fields=fields,
                start_date=start_date,
            )

        return AssessmentHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_barrier_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="barrier",
                fields=fields,
                start_date=start_date,
            )

        return BarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_notes_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="note",
                fields=fields,
                start_date=start_date,
            )

        return NoteHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_public_barrier_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="public_barrier",
                fields=fields,
                start_date=start_date,
            )

        return PublicBarrierHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_public_barrier_notes_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="public_barrier_note",
                fields=fields,
                start_date=start_date,
            )

        return PublicBarrierNoteHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_team_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="team_member",
                fields=fields,
                start_date=start_date,
            )

        return TeamMemberHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )

    @classmethod
    def get_wto_history(cls, barrier_id, fields=(), start_date=None, use_cache=False):
        if use_cache:
            return cls.get_cached_history_items(
                barrier_id,
                model="wto",
                fields=fields,
                start_date=start_date,
            )

        return WTOHistoryFactory.get_history_items(
            barrier_id=barrier_id,
            fields=fields,
            start_date=start_date,
        )
