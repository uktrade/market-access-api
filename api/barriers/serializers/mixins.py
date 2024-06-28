from rest_framework import serializers


class LocationFieldMixin(metaclass=serializers.SerializerMetaclass):
    # Use metaclass to get the fields registered at the serializer where the mixin is used
    # The field will need to be listed on the serializer using this mixin
    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        try:
            return obj.location or ""
        except AttributeError:
            return ""
