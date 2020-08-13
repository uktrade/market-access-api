from .base import BaseHistoryItem


class BaseWTOHistoryItem(BaseHistoryItem):
    model = "wto_profile"


class CaseNumberHistoryItem(BaseWTOHistoryItem):
    field = "case_number"


class CommitteeNotificationDocumentHistoryItem(BaseWTOHistoryItem):
    field = "committee_notification_document"

    def get_value(self, record):
        if record.committee_notification_document:
            return {
                "id": str(record.committee_notification_document.id),
                "name": record.committee_notification_document.original_filename,
            }


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

    def get_value(self, record):
        if record.meeting_minutes:
            return {
                "id": str(record.meeting_minutes.id),
                "name": record.meeting_minutes.original_filename,
            }


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
