from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.template.defaultfilters import pluralize

from api.user.models import get_my_barriers_saved_search, get_team_barriers_saved_search

from notifications_python_client.notifications import NotificationsAPIClient


def get_saved_search_as_dict(saved_search):
    data = {
        "name": saved_search.name,
    }
    if saved_search.notify_about_additions:
        data["added_barriers"] = [
            {
                "code": barrier.code,
                "title": barrier.barrier_title,
            }
            for barrier in saved_search.new_barriers_since_notified
        ]
    if saved_search.notify_about_updates:
        data["updated_barriers"] = [
            {
                "code": barrier.code,
                "title": barrier.barrier_title,
            }
            for barrier in saved_search.updated_barriers_since_notified
        ]
    return data


def get_saved_searches_markdown(saved_searches):
    markdown = ""

    for saved_search in saved_searches:
        markdown += f"#{saved_search.name}\n"

        if saved_search.notify_about_additions:
            new_count = saved_search.new_count_since_notified
            if new_count:
                markdown += f"*{new_count} barrier{pluralize(new_count)} added\n"

        if saved_search.notify_about_updates:
            updated_count = saved_search.updated_count_since_notified
            if updated_count:
                markdown += f"*{updated_count} barrier{pluralize(updated_count)} updated\n"

        markdown += "\n---\n"

    return markdown


def send_email(user, saved_searches):

    api_key = "dev-be2cd742-a94b-4e9b-9bb4-ce4284e68f69-bdafd5ed-09aa-4361-8af1-a41d5a719756"
    client = NotificationsAPIClient(api_key)
    response = client.send_email_notification(
        email_address=user.email,
        template_id='24e8d95b-b61e-4c3b-95ae-3d085147725b',
        personalisation={
            "first_name": user.first_name,
            "saved_searches": get_saved_searches_markdown(saved_searches),
            "dashboard_link": "link",
        }
    )


def mark_user_saved_searches_as_notified(user):
    my_barriers = get_my_barriers_saved_search(user)
    my_barriers.mark_as_notified()

    team_barriers = get_team_barriers_saved_search(user)
    team_barriers.mark_as_notified()

    for saved_search in user.saved_searches.all():
        saved_search.mark_as_notified()


def get_saved_searches_for_notification(user):
    my_barriers = get_my_barriers_saved_search(user)
    team_barriers = get_team_barriers_saved_search(user)

    saved_searches = []

    if my_barriers.should_notify():
        saved_searches.append(my_barriers)

    if team_barriers.should_notify():
        saved_searches.append(team_barriers)

    for saved_search in user.saved_searches.all():
        if saved_search.should_notify():
            saved_searches.append(saved_search)

    return saved_searches



class Command(BaseCommand):
    help = "Sends notification emails about additions and updates to saved searches"

    def handle(self, *args, **options):
        User = get_user_model()
        count = 0

        for user in User.objects.all():
            saved_searches = get_saved_searches_for_notification(user)
            if saved_searches:
                send_email(user, saved_searches)
                count += 1
            mark_user_saved_searches_as_notified(user)

        self.stdout.write(
            self.style.SUCCESS(f"Success: {count} notification emails sent")
        )
