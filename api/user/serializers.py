from rest_framework import serializers

from django.contrib.auth import get_user_model

UserModel = get_user_model()


class WhoAmISerializer(serializers.ModelSerializer):
    """User serializer"""

    class Meta:
        model = UserModel
        fields = (
            'username',
            'last_login',
            'first_name',
            'last_name',
            'email',
        )
        depth = 1
