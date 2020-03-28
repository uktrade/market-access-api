from model_utils import Choices

PROBLEM_STATUS_TYPES = Choices(
    (1, "A problem that is blocking a specific export or investment"),
    (2, "A strategic barrier likely to affect multiple exports or sectors"),
)

ESTIMATED_LOSS_RANGE = Choices(
    (1, "Less than £1m"), (2, "£1m to £10m"), (3, "£10m to £100m"), (4, "Over £100m")
)

STAGE_STATUS = Choices((1, "NOT STARTED"), (2, "IN PROGRESS"), (3, "COMPLETED"))

GOVT_RESPONSE = Choices(
    (1, "None, this is for our information only at this stage"),
    (2, "In-country support from post"),
    (3, "Broader UK government sensitivities"),
)

PUBLISH_RESPONSE = Choices(
    (1, "Yes"), (2, "No"), (3, "Don't publish without consultation")
)

SUPPORT_TYPE = Choices(
    (1, "Market access team to provide support on next steps"),
    (2, "None, I’m going to handle next steps myself as the lead coordinator"),
)

REPORT_STATUS = Choices(
    (0, "Unfinished"),
    (1, "AwaitingScreening"),
    (2, "Accepted"),
    (3, "Rejected"),
    (4, "Archived"),
)

RESOLVED_STATUS = Choices(
    (3, "Resolved: In part"),
    (4, "Resolved: In full"),
)

BARRIER_STATUS = Choices(
    (0, "Unfinished"),
    (1, "Open: Pending action"),
    (2, "Open: In progress"),
    (5, "Dormant"),
    (6, "Archived"),
    (7, 'Unknown'),
) + RESOLVED_STATUS

BARRIER_PENDING = Choices(
    ("UK_GOVT", "UK government"),
    ("FOR_GOVT", "Foreign government"),
    ("BUS", "Affected business"),
    ("OTHER", "Other")
)

BARRIER_TYPE_CATEGORIES = Choices(
    ("GOODS", "Goods"),
    ("SERVICES", "Services"),
    ("GOODSANDSERVICES", "Goods and Services"),
)

BARRIER_CHANCE_OF_SUCCESS = Choices(
    ("HIGHLY_LIKELY", "Highly likely"),
    ("LIKELY", "Likely"),
    ("UNLIKELY", "Unlikely"),
    ("HIGHLY_UNLIKELY", "Highly unlikely"),
)

BARRIER_INTERACTION_TYPE = Choices(("COMMENT", "Comment"))

CONTRIBUTOR_TYPE = Choices(
    ("INITIATOR", "Initiator"), ("CONTRIBUTOR", "Contributor"), ("LEAD", "Lead")
)

BARRIER_SOURCE = Choices(
    ("COMPANY", "Company"),
    ("TRADE", "Trade association"),
    ("GOVT", "Government entity"),
    ("OTHER", "Other"),
)

TIMELINE_EVENTS = Choices(
    ("REPORT_CREATED", "Report Created"),
    ("BARRIER_CREATED", "Barrier Created"),
    ("BARRIER_STATUS_CHANGE", "Barrier Status Change"),
)

ASSESMENT_IMPACT = Choices(
    ("HIGH", "High"),
    ("MEDIUMHIGH", "Medium High"),
    ("MEDIUMLOW", "Medium Low"),
    ("LOW", "Low"),
)

BARRIER_ARCHIVED_REASON = Choices(
    ("DUPLICATE", "Duplicate"),
    ("NOT_A_BARRIER", "Not a barrier"),
    ("OTHER", "Other"),
)
