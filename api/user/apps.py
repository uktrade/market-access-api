from django.apps import AppConfig
from django.contrib.auth import get_user_model
from simple_history import models, register


class UserConfig(AppConfig):
    name = "api.user"

    def ready(self):
        # we want to register the UserGroup model with simple_history so that changes to group memberships are tracked.
        user_model = get_user_model()

        # we need to check if the model has already been registered as the ready() function can run multiple times
        # in local development
        if user_model not in models.registered_models.values():
            # registering the through table with simple_history, migrations will live in the user app
            register(user_model, app=__package__, m2m_fields=[user_model.groups.field])
