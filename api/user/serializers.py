from rest_framework import serializers

from django.contrib.auth.models import User


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    class Meta:
        model = User
        fields = (
            'last_login',
            'first_name',
            'last_name',
            'email',
        )
        depth = 1
