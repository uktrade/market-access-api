from rest_framework import serializers

from django.contrib.auth import get_user_model


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    class Meta:
        model = get_user_model()
        fields = (
            'last_login',
            'first_name',
            'last_name',
            'email',
        )
        depth = 1
