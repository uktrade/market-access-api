from api.wto.models import WTOProfile
from api.barriers.models import BarrierInstance
from .base import BaseHistoryItem, HistoryItemFactory


class BaseWTOHistoryItem(BaseHistoryItem):
    model = "wto_profile"


class CaseNumberHistoryItem(BaseWTOHistoryItem):
    field = "case_number"


class CommitteeNotificationDocumentHistoryItem(BaseWTOHistoryItem):
    field = "committee_notification_document"


class CommitteeNotificationLinkHistoryItem(BaseWTOHistoryItem):
    field = "committee_notification_link"


class CommitteeNotifiedHistoryItem(BaseWTOHistoryItem):
    field = "committee_notified"

    def get_value(self, record):
        if record.committee_notified:
            return {
                "id": record.committee_notified.id,
                "name": record.committee_notified.name,
            }


class CommitteeRaisedInHistoryItem(BaseWTOHistoryItem):
    field = "committee_raised_in"

    def get_value(self, record):
        if record.committee_raised_in:
            return {
                "id": record.committee_raised_in.id,
                "name": record.committee_raised_in.name,
            }


class MeetingMinutesHistoryItem(BaseWTOHistoryItem):
    field = "meeting_minutes"


class MemberStatesHistoryItem(BaseWTOHistoryItem):
    field = "member_states"


class RaisedDateHistoryItem(BaseWTOHistoryItem):
    field = "raised_date"


class WTONotifiedStatusHistoryItem(BaseWTOHistoryItem):
    field = "wto_notified_status"

    def get_value(self, record):
        return {
            "wto_has_been_notified": record.wto_has_been_notified,
            "wto_should_be_notified": record.wto_should_be_notified,
        }


class WTOHistoryFactory(HistoryItemFactory):
    """
    Polymorphic wrapper for wto HistoryItem classes
    """

    class_lookup = {}
    history_item_classes = (
        CaseNumberHistoryItem,
        CommitteeNotificationDocumentHistoryItem,
        CommitteeNotificationLinkHistoryItem,
        CommitteeNotifiedHistoryItem,
        CommitteeRaisedInHistoryItem,
        MeetingMinutesHistoryItem,
        MemberStatesHistoryItem,
        RaisedDateHistoryItem,
        WTONotifiedStatusHistoryItem,
    )
    history_types = ("~", "+")

    @classmethod
    def get_history(cls, barrier_id, start_date=None):
        barrier = BarrierInstance.objects.get(pk=barrier_id)
        if barrier.wto_profile:
            history = WTOProfile.history.filter(id=barrier.wto_profile.id)
            if start_date:
                history = history.filter(history_date__gt=start_date)
            return history.order_by("history_date")
        return []
