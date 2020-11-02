from rest_framework import serializers


class ArchivedField(serializers.BooleanField):
    def custom_update(self, validated_data):
        instance = self.parent.instance
        user = self.parent.context["request"].user
        archived = validated_data.pop("archived")

        if instance.archived is False and archived is True:
            instance.archive(
                user=user,
                reason=validated_data.pop("archived_reason", None),
                commit=False,
            )
        elif instance.archived is True and archived is False:
            instance.unarchive(
                user=user,
                reason=validated_data.pop("unarchived_reason", None),
                commit=False,
            )


class ApprovedField(serializers.BooleanField):
    def custom_update(self, validated_data):
        instance = self.parent.instance
        user = self.parent.context["request"].user
        approved = validated_data.pop("approved")

        if instance.approved is not True and approved is True:
            instance.approve(user=user, commit=False)
        elif instance.approved is not False and approved is False:
            instance.reject(user=user, archive=True, commit=False)
