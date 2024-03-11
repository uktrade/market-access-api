from model_utils.choices import Choices


class UserRoles:
    """
    Group based roles, the groups were created in ./api/user/migrations/0015_assign_publish_permissions.py
    """

    APPROVER = "Public barrier approver"
    PUBLISHER = "Publisher"
    ADMIN = "Administrator"


USER_ACTIVITY_EVENT_TYPES = Choices(
    ("USER_LOGGED_IN", "User logged in"),
    # Logout event is not currently used on the front end
    # ("USER_LOGGED_OUT", "User logged out"),
    ("BARRIER_CSV_DOWNLOAD", "Barrier CSV download"),
    ("START_DAY_ACTIVITY", "Start day activity"),
    ("END_DAY_ACTIVITY", "End day activity"),
)
