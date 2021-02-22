from rest_framework import serializers

from api.metadata.fields import CountryListField

from .fields import WTOCommitteeField
from .models import WTOProfile


class WTOProfileSerializer(serializers.ModelSerializer):
    committee_notification_document = serializers.SerializerMethodField()
    meeting_minutes = serializers.SerializerMethodField()
    member_states = CountryListField(required=False)
    committee_notified = WTOCommitteeField(required=False)
    committee_raised_in = WTOCommitteeField(required=False)

    class Meta:
        model = WTOProfile
        fields = (
            "id",
            "wto_has_been_notified",
            "wto_should_be_notified",
            "committee_notified",
            "committee_notification_link",
            "committee_notification_document",
            "member_states",
            "committee_raised_in",
            "meeting_minutes",
            "raised_date",
            "case_number",
        )
        read_only_fields = ("id",)

    def get_serialized_document(self, document):
        if document is not None:
            return {
                "id": document.id,
                "name": document.original_filename,
                "size": document.size,
                "status": document.document.status,
            }

    def get_committee_notification_document(self, obj):
        return self.get_serialized_document(obj.committee_notification_document)

    def get_meeting_minutes(self, obj):
        return self.get_serialized_document(obj.meeting_minutes)
