from model_utils import Choices

PROBLEM_STATUS_TYPES = Choices(
    (1, "A procedural, short-term barrier"),
    (2, "A long-term strategic barrier"),
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


class StatusNameMixin:
    choices = Choices()

    @classmethod
    def name(cls, status):
        """
        Return the name/label of the gives status.
        :param status: INT
        :return:
        """
        d = dict(cls.choices)
        return d[status]


class BarrierStatus(StatusNameMixin):
    UNFINISHED = 0
    OPEN_PENDING = 1
    OPEN_IN_PROGRESS = 2
    RESOLVED_IN_PART = 3
    RESOLVED_IN_FULL = 4
    DORMANT = 5
    ARCHIVED = 6
    UNKNOWN = 7

    choices = Choices(
        (UNFINISHED, "Unfinished"),
        (OPEN_PENDING, "Open: Pending action"),
        (OPEN_IN_PROGRESS, "Open: In progress"),
        (RESOLVED_IN_PART, "Resolved: In part"),
        (RESOLVED_IN_FULL, "Resolved: In full"),
        (DORMANT, "Dormant"),
        (ARCHIVED, "Archived"),
        (UNKNOWN, 'Unknown'),
    )


class PublicBarrierStatus(StatusNameMixin):
    UNKNOWN = 0
    INELIGIBLE = 10
    ELIGIBLE = 20
    READY = 30
    PUBLISHED = 40
    UNPUBLISHED = 50

    choices = Choices(
        (UNKNOWN, "To be decided"),
        (INELIGIBLE, "Not for public view"),
        (ELIGIBLE, "Allowed"),
        (READY, "Ready"),
        (PUBLISHED, "Published"),
        (UNPUBLISHED, "Unpublished")
    )


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

TRADE_DIRECTION_CHOICES = Choices(
    (1, "Exporting from the UK or investing overseas"),
    (2, "Importing or investing into the UK")
)
