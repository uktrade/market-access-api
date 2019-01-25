import json
import os
import requests
import textwrap

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import intword
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Sum
from django.utils import timezone

from ...models import BarrierInstance


class Command(BaseCommand):
    """ send stats of Barriers into preferred output channel, terminal or slack or email """
    help = "collects and posts barrier statistics to chosen channel"

    def add_arguments(self, parser):
        parser.add_argument(
            "days",
            nargs="+",
            type=int,
            help="number of days to run reports for"
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output the statistics in JSON format."
        )
        parser.add_argument(
            "--print",
            action="store_true",
            help="Output the statistics to terminal in text format."
        )
        parser.add_argument(
            "--slack",
            action="store_true",
            help="Output the statistics to a slack channel"
        )
        parser.add_argument(
            "--email",
            action="store_true",
            help="Email statistics"
        )

    def handle(self, *args, **options):

        barriers = BarrierInstance.barriers.all()
        reports = BarrierInstance.reports.all()
        user_model = get_user_model()
        users = user_model.objects.all()

        days = options["days"][0]
        days_ago = timezone.now() - relativedelta(days=days)

        stats = {
            "barriers": {
                "total_count": barriers.count(),
                "submitted_count": barriers.filter(reported_on__gt=days_ago).count(),
                "modified_count": barriers.filter(modified_on__gt=days_ago).count(),
            },
            "reports": {
                "total_count": reports.count()
            },
            "users": {
                "total_count": users.distinct().count(),
                "active_count": users.filter(last_login__gt=days_ago).distinct().count()
            }
        }

        if options["json"]:
            return self._handle_json(stats)

        stats_txt = self._generate_txt(stats, days)

        if options["print"]:
            return stats_txt

        if options["slack"]:
            self._report_to_slack(stats_txt)

        if options["email"]:
            send_to_addresses = os.getenv("STATS_EMAILS").split(',')
            send_mail(
                "Export Wins statistics",
                stats_txt,
                settings.SENDING_ADDRESS,
                send_to_addresses,
            )

    def _generate_txt(self, stats, days):
        barriers = stats["barriers"]
        reports = stats["reports"]
        users = stats["users"]
        stats_txt = """
            BARRIERS:

            Number of barriers added to the service in last {} days: {} 
            Number of barriers modified in last {} days: {}
            Barriers modified in last {} days: {}

            UNFINISHED REPORTS:

            Current number of unfinished reports: {}

            USERS:

            Amount  of registered users for the service: {}
            Number of users logged in within last {} days: {}

            """.format(
            days, barriers["total_count"],
            days, barriers["submitted_count"],
            days, barriers["modified_count"],
            reports["total_count"],
            users["total_count"],
            days, users["active_count"]
        )
        return textwrap.dedent(stats_txt)

    @staticmethod
    def _handle_json(stats):
        return json.dumps(stats, separators={",", ":"})

    def _report_to_slack(self, stats):
        messages = self._split_and_format_slack_message(stats)   # split in multiple messages
        webhook_url = settings.SLACK_WEBHOOK
        for msg in messages:
            slack_data = {'text': msg, 'mrkdwn': 'true', 'title': 'Datahub CSV Validation'}
            response = requests.post(
                webhook_url, data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s'
                    % (response.status_code, response.text)
                )

    def _split_and_format_slack_message(self, message):
        messages, lines = [], message.splitlines()
        msg, idx = "", 1
        for line in lines:
            msg += line + "\n"
            if idx % 30 == 0:
                messages.append("```\n" + msg + "```")
                msg = ""
            idx += 1
        messages.append("```\n" + msg + "```")
        return messages