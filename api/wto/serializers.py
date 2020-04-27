from .models import WTOProfile

from rest_framework import serializers


class WTOProfileSerializer(serializers.ModelSerializer):
    committee_notification_document = serializers.SerializerMethodField()

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
        read_only_fields = ("id", )

    def get_committee_notification_document(self, obj):
        if obj.committee_notification_document is None:
            return None

        document = obj.committee_notification_document
        return {
            "id": document.id,
            "name": document.original_filename,
            "size": document.size,
            "status": document.document.status,
        }
