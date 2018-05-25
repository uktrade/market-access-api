from rest_framework import serializers

from api.barriers.models import Barrier
from api.barriers.company import Company


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = [
            'id',
            'title',
            'description',
            'status',
            'is_emergency',
            'company_id',
            'company_name',
            'export_country',
            'created_on',
        ]


class BarrierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = [
            'id',
            'title',
            'description',
            'status',
            'is_emergency',
            'company_id',
            'company_name',
            'export_country',
            'created_on',
        ]


# class CompanySerializer(serializers.Serializer):
#     id = serializers.UUIDField(read_only=True)
#     name = serializers.CharField(required=True, allow_blank=False, max_length=255)
#     comanies_house_no = serializers.CharField(required=False, allow_blank=True, max_length=255)
#     address = serializers.CharField(required=False, allow_blank=True, max_length=255)
#     sector_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
#     incorporation_date = serializers.CharField(required=False, allow_blank=True, max_length=255)
#     company_type = serializers.CharField(required=False, allow_blank=True, max_length=255)
#     turnover_range = serializers.CharField(required=False, allow_blank=True, max_length=255)
#     employee_range = serializers.CharField(required=False, allow_blank=True, max_length=255)


# class BarrierDetailBaseSerializer(serializers.BaseSerializer):
#     def to_representation(self, obj):
#         company = Company(obj.id)
#         return {
#             'id': obj.id,
#             'name': obj.name,
#             'company': {
#                 'company_id': comapny.id,
#                 'company_name': company.name
#             }
#         }


# class CompanyRelatedFieldSerializer(serializers.BaseSerializer):
#     def to_representation(self, id):
#         company = Company(id)
#         company_json = {
#             'company_id': company.id,
#             'company_name': company.name,
#         }
#         return company_json


# class BarrierDetailSerializer(serializers.Serializer):
#     id = serializers.IntegerField(read_only=True)
#     title = serializers.CharField(required=True, allow_blank=False, max_length=255)
#     description = serializers.CharField(required=True, allow_blank=False)
#     status = serializers.BooleanField(required=False)
#     is_emergency = serializers.BooleanField(required=False)
#     company = CompanyRelatedFieldSerializer(id)

#     def create(self, validated_data):
#         """
#         Create and return a new `Barrier` instance, given the validated data.
#         """
#         return Barrier.objects.create(**validated_data)

#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Barrier` instance, given the validated data.
#         """
#         instance.title = validated_data.get('title', instance.title)
#         instance.save()
#         return instance
