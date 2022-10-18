from django.conf import settings
from django.utils import timezone

from api.user.constants import USER_ACTIVITY_EVENT_TYPES
from api.user.models import UserActvitiyLog


class UserActivityLogMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_request(self, request):

        if request.user.is_authenticated():

            user = request.user

            local_timezone = settings.LOCAL_TIME_ZONE

            # if first activity today at LOCAL_TIME_ZONE
            # midnight at timezone astimezone
            start_of_day = (
                timezone.now()
                .astimezone(local_timezone)
                .replace(hour=0, minute=0, second=0, microsecond=0)
            )
            last_activity = user.profile.last_activity
            if (last_activity) and (last_activity < start_of_day):
                UserActvitiyLog.objects.create(
                    user=request.user,
                    event_type=USER_ACTIVITY_EVENT_TYPES.END_DAY_ACTIVITY,
                    event_description="End of day activity",
                    event_time=last_activity,
                )
            new_last_activity = timezone.now()
            UserActvitiyLog.objects.create(
                user=request.user,
                event_type=USER_ACTIVITY_EVENT_TYPES.START_DAY_ACTIVITY,
                event_description="Start day activity",
                event_time=new_last_activity,
            )
            profile = user.profile
            profile.last_activity = new_last_activity
            profile.save()

        return None
