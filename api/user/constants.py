from model_utils.choices import Choices


class UserRoles:
    """
    Group based roles, the groups were created in ./api/user/migrations/0015_assign_publish_permissions.py
    """

    APPROVER = "Public barrier approver"
    PUBLISHER = "Publisher"
    ADMIN = "Administrator"


ADMIN_PROTECTED_USER_FIELDS = [
    "groups",
    "username",
    "password",
    "last_login",
    "is_superuser",
    "is_staff",
    "is_active",
    "date_joined",
    "user_permissions",
]

USER_ACTIVITY_EVENT_TYPES = Choices(
    ("USER_LOGGED_IN", "User logged in"),
    # Logout event is not currently used on the front end
    # ("USER_LOGGED_OUT", "User logged out"),
    ("BARRIER_CSV_DOWNLOAD", "Barrier CSV download"),
    ("START_DAY_ACTIVITY", "Start day activity"),
    ("END_DAY_ACTIVITY", "End day activity"),
)
