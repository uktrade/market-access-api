from rest_framework import serializers

from api.barriers.models import ExampleThing


class ExampleThingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleThing
        fields = ["id", "name"]


class ExampleThingField(serializers.ListField):
    def to_representation(self, example_things):
        serializer = ExampleThingSerializer(example_things.all(), many=True)
        return serializer.data
