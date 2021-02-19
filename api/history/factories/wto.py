from api.wto.models import WTOProfile

from ..items.wto import (CaseNumberHistoryItem,
                         CommitteeNotificationDocumentHistoryItem,
                         CommitteeNotificationLinkHistoryItem,
                         CommitteeNotifiedHistoryItem,
                         CommitteeRaisedInHistoryItem,
                         MeetingMinutesHistoryItem, MemberStatesHistoryItem,
                         RaisedDateHistoryItem, WTONotifiedStatusHistoryItem)
from .base import HistoryItemFactoryBase


class WTOHistoryFactory(HistoryItemFactoryBase):
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
    def get_history(cls, barrier_id):
        return WTOProfile.history.filter(barrier_id=barrier_id).order_by("history_date")
