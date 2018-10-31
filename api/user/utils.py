from django.contrib.auth import get_user_model

from .models import Profile

UserModel = get_user_model()

def has_profile(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return False