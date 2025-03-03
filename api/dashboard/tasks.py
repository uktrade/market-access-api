from datetime import datetime

import pytz

from api.core.date_utils import get_nth_day_of_month


def create_erd_review_task():
    return {
        "tag": "ERD REVIEW",
        "message": [
            "Review",
            "estimated resolution date change request",
        ],
        "task_url": "barriers:review_estimated_resolution_date",
        "link_text": "Review",
    }


def create_editor_task(barrier):
    overdue = (
        barrier["deadline"].replace(tzinfo=None) < datetime.today()
        if barrier["deadline"]
        else ""
    )
    deadline = barrier["deadline"].strftime("%d %B %Y") if barrier["deadline"] else ""
    if barrier["public_barrier_title"] and barrier["public_barrier_summary"]:
        return {
            "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
            "message": [
                "Submit for clearance checks and GOV.UK publication approval",
                f"by {deadline}." if deadline else "",
            ],
            "task_url": "barriers:public_barrier_detail",
            "link_text": "Submit for clearance checks and GOV.UK publication approval",
        }
    else:
        return {
            "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
            "message": [
                "Add a public title and summary",
                "to this barrier before it can be approved.",
                f"This needs to be done by {deadline}." if deadline else "",
            ],
            "task_url": "barriers:public_barrier_detail",
            "link_text": "Add a public title and summary",
        }


def create_approver_task(barrier):
    overdue = (
        barrier["deadline"].replace(tzinfo=None) < datetime.today()
        if barrier["deadline"]
        else ""
    )
    deadline = barrier["deadline"].strftime("%d %B %Y") if barrier["deadline"] else ""

    return {
        "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
        "message": [
            "Approve this barrier",
            (
                f"for publication and complete clearance checks by {deadline}."
                if deadline
                else ""
            ),
            "It can then be submitted to the GOV.UK content team.",
        ],
        "task_url": "barriers:public_barrier_detail",
        "link_text": "Approve this barrier",
    }


def create_publisher_task(barrier):
    overdue = (
        barrier["deadline"].replace(tzinfo=None) < datetime.today()
        if barrier["deadline"]
        else ""
    )
    deadline = barrier["deadline"].strftime("%d %B %Y") if barrier["deadline"] else ""

    return {
        "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
        "message": [
            "Complete GOV.UK content checks",
            f"by {deadline}." if deadline else "",
        ],
        "task_url": "barriers:public_barrier_detail",
        "link_text": "Complete GOV.UK content checks",
    }


def create_barrier_entry(barrier):
    return {
        "barrier_id": str(barrier["id"]),
        "barrier_code": barrier["code"],
        "barrier_title": barrier["title"],
        "modified_by": barrier["full_name"],
        "modified_on": (
            barrier["modified_on"].strftime("%d %B %Y")
            if barrier["modified_on"]
            else "Unknown"
        ),
        "task_list": [],
    }


def create_progress_update_task(barrier):
    today = datetime.today()
    first_of_month_date = today.replace(day=1, tzinfo=pytz.UTC)
    third_friday_day = get_nth_day_of_month(
        year=today.year, month=today.month, nth=3, weekday=4
    )
    third_fridate_date = today.replace(day=third_friday_day)
    if not barrier["progress_update_modified_on"] or (
        barrier["progress_update_modified_on"] < first_of_month_date
        and today < third_fridate_date
    ):
        tag = "PROGRESS UPDATE DUE"
    elif (
        barrier["progress_update_modified_on"] < first_of_month_date
        and today > third_fridate_date
    ):
        tag = "OVERDUE PROGRESS UPDATE"
    else:
        return

    return {
        "tag": tag,
        "message": [
            "Add a monthly progress update",
            f"to this PB100 barrier by {third_fridate_date.strftime('%d %B %Y')}.",
        ],
        "task_url": "barriers:add_progress_update",
        "link_text": "Add a monthly progress update",
    }


def create_next_step_task(_):
    return {
        "tag": "REVIEW NEXT STEP",
        "message": [
            "Review the barrier next steps",
        ],
        "task_url": "barriers:list_next_steps",
        "link_text": "Review the next steps",
    }


def create_overseas_task(_):
    return {
        "tag": "PROGRESS UPDATE DUE",
        "message": [
            "Add a quarterly progress update",
            "to this overseas delivery barrier.",
        ],
        "task_url": "barriers:add_progress_update",
        "link_text": "Add a quarterly progress update",
    }


def create_programme_fund_update_task(_):
    return {
        "tag": "PROGRESS UPDATE DUE",
        "message": ["Add a programme fund update", "to this barrier."],
        "task_url": "barriers:add_programme_fund_progress_update",
        "link_text": "Add a programme fund update",
    }


def create_missing_hs_code_task(_):
    return {
        "tag": "ADD INFORMATION",
        "message": ["Add an HS code to this barrier."],
        "task_url": "barriers:edit_commodities",
        "link_text": "Add an HS code to this barrier.",
    }


def create_missing_gov_org_task(_):
    return {
        "tag": "ADD INFORMATION",
        "message": [
            "Check and add any other government departments (OGDs)",
            "involved in the resolution of this barrier.",
        ],
        "task_url": "barriers:edit_gov_orgs",
        "link_text": "Check and add any other government departments (OGDs)",
    }


def create_add_progress_update_task(_):
    return {
        "tag": "ADD INFORMATION",
        "message": [
            "Add your delivery confidence",
            "to this barrier.",
        ],
        "task_url": "barriers:add_progress_update",
        "link_text": "Add your delivery confidence",
    }


def create_overdue_erd_task(barrier):
    return {
        "tag": "CHANGE OVERDUE",
        "message": [
            "Review the estimated resolution date",
            f"as it is currently listed as {barrier['estimated_resolution_date']},",
            "which is in the past.",
        ],
        "task_url": "barriers:edit_estimated_resolution_date",
        "link_text": "Review the estimated resolution date",
    }


def create_add_priority_erd_task(_):
    return {
        "tag": "ADD DATE",
        "message": [
            "Add an estimated resolution date",
            "to this PB100 barrier.",
        ],
        "task_url": "barriers:edit_estimated_resolution_date",
        "link_text": "Add an estimated resolution date",
    }


def create_review_priority_erd_task(barrier):
    return {
        "tag": "REVIEW DATE",
        "message": [
            "Check the estimated resolution date",
            f"as it has not been reviewed since {barrier['progress_update_modified_on'].strftime('%d %B %Y')}.",
        ],
        "task_url": "barriers:edit_estimated_resolution_date",
        "link_text": "Check the estimated resolution date",
    }


def create_mentions_task(mention):
    return {
        "tag": "REVIEW COMMENT",
        "message": [
            "Reply to the comment",
            f"{mention['first_name']} {mention['last_name']} mentioned you in on",
            f"{mention['created_on'].strftime('%d %B %Y')}.",
        ],
        "task_url": "barriers:barrier_detail",
        "link_text": "Reply to the comment",
    }
