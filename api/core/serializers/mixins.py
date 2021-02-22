from collections import OrderedDict

from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject


class AllowNoneAtToRepresentationMixin:
    """
    Patch DRF to allow to_representation to be called for fields with None values.
    To be used with ModelSerializers
    """

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            if isinstance(attribute, PKOnlyObject):
                if attribute.pk is None:
                    ret[field.field_name] = None
            else:
                # >> Override DRF here
                # Deliberately run `to_representation` for `None` values so that
                # custom formatting can be applied.
                ret[field.field_name] = field.to_representation(attribute)

        return ret


class CustomUpdateMixin:
    """
    Allows a serializer's fields to have custom_update functions
    """

    def update(self, instance, validated_data):
        for field in self._writable_fields:
            if hasattr(field, "custom_update") and field.source in validated_data:
                field.custom_update(validated_data)

        return super().update(instance, validated_data)


class AuditMixin:
    """
    Automatically update created_by and modified_by fields
    """

    def get_user(self):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user

    def create(self, validated_data):
        user = self.get_user()
        if user:
            validated_data["created_by"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.get_user()
        if user:
            validated_data["modified_by"] = user
        return super().update(instance, validated_data)
