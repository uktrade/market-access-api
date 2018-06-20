from model_utils import Choices

PROBLEM_STATUS_TYPES = Choices(
    (1, "It hasn't happened yet"),
    (2, "It's happening now"),
    (3, "It happened in the past"),
)

ESTIMATED_LOSS_RANGE = Choices(
    (1, "Less than £1m"),
    (2, "£1m to £10m"),
    (3, "£10m to £100m"),
    (4, "Over £100m"),
)

STAGE_STATUS = Choices(
    (1, "NOT STARTED"),
    (2, "IN PROGRESS"),
    (3, "COMPLETED"),
)

ADV_BOOLEAN = Choices(
    (1, "Yes"),
    (2, "No"),
    (3, "Don't know")
)

GOVT_RESPONSE = Choices(
    (1, "None, this is for our information only at this stage"),
    (2, "In-country support from post"),
    (3, "Broader UK government sensitivities")
)

PUBLISH_RESPONSE = Choices(
    (1, "Yes"),
    (2, "No"),
    (3, "Don't publish without consultation")
)

SUPPORT_TYPE = Choices(
    (1, "Market access team to take over the lead"),
    (2, "Trade barriers team to guide me on next steps"),
    (3, "None, I'm going to hendle next steps myself")
)

REPORT_STATUS = Choices(
    (0, 'Unfinished'),
    (1, 'AwaitingScreening'),
    (2, 'Accepted'),
    (3, 'Rejected'),
    (4, 'Archived')
)

BARRIER_STATUS = Choices(
    (0, 'Unfinished'),
    (1, 'Screening'),
    (2, 'Assesment'),
    (3, 'Rejected'),
    (4, 'Resolved'),
    (5, 'Hibernated'),
    (6, 'Archived')
)
