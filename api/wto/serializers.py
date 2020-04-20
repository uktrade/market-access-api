from .models import WTOProfile

from rest_framework import serializers


class WTOProfileSerializer(serializers.ModelSerializer):

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
