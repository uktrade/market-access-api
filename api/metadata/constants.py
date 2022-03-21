from model_utils import Choices

BARRIER_TERMS = Choices(
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
        (UNKNOWN, "Unknown"),
    )


class PublicBarrierStatus(StatusNameMixin):
    UNKNOWN = 0
    INELIGIBLE = 10
    ELIGIBLE = 20
    READY = 30
    PUBLISHED = 40
    UNPUBLISHED = 50
    REVIEW_LATER = 60

    choices = Choices(
        (UNKNOWN, "Not yet sifted"),
        (INELIGIBLE, "Not allowed"),
        (ELIGIBLE, "Allowed"),
        (READY, "Ready"),
        (PUBLISHED, "Published"),
        (UNPUBLISHED, "Unpublished"),
        (REVIEW_LATER, "Review later"),
    )


BARRIER_PENDING = Choices(
    ("UK_GOVT", "UK government"),
    ("FOR_GOVT", "Foreign government"),
    ("BUS", "Affected business"),
    ("OTHER", "Other"),
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

TRADE_CATEGORIES = Choices(
    ("GOODS", "Goods"),
    ("SERVICE", "Service"),
    ("INVESTMENT", "Investment"),
    ("PROCUREMENT", "Procurement"),
    ("OTHER", "Other"),
)

ECONOMIC_ASSESSMENT_RATING = Choices(
    ("HIGH", "High"),
    ("MEDIUMHIGH", "Medium High"),
    ("MEDIUMLOW", "Medium Low"),
    ("LOW", "Low"),
)

PROGRESS_UPDATE_CHOICES = Choices(
    ("ON_TRACK", "On track"),
    ("RISK_OF_DELAY", "Risk of delay"),
    ("DELAYED", "Delayed"),
)

ECONOMIC_ASSESSMENT_IMPACT = Choices(
    (1, "1: £ less than a thousand"),
    (2, "2: £ tens of thousands"),
    (3, "3: £ hundreds of thousands"),
    (4, "4: £ millions"),
    (5, "5: £ tens of millions"),
    (6, "6: £ hundreds of millions"),
    (7, "7: £ billions"),
    (8, "8: £ tens of billions"),
)

RESOLVABILITY_ASSESSMENT_TIME = Choices(
    (0, "0: not resolvable"),
    (1, "1: longer than 5 years"),
    (2, "2: 3 to 5 years"),
    (3, "3: 1 to 3 years"),
    (4, "4: within a year"),
)

RESOLVABILITY_ASSESSMENT_EFFORT = Choices(
    (0, "0: Not resolvable"),
    (1, "1: Highly resource intensive (significant resources needed)"),
    (
        2,
        "2: substantial resources required (extras or significant reprioritisation of exsiting resources needed)",
    ),
    (
        3,
        "3: moderate resources required (low or moderate prioritisation or resources needed)",
    ),
    (4, "4: low resource requirement (can be delivered within existing resources)"),
)

STRATEGIC_ASSESSMENT_SCALE = Choices(
    (
        1,
        "1: 3 or more government wide objectives, or poses medium/high risk to delivery "
        "of one of government wide objectives and/or potential for significant PR issues.",
    ),
    (
        2,
        "2: 1 or 2 government wide objectives but does not pose much risk for PR or objective delivery",
    ),
    (3, "3: neutral to government wide objectives"),
    (4, "4: supports 1 or 2  government wide objectives"),
    (
        5,
        "5: substantial contribution to 1 strategic objective or supporting 3 or more strategic objectives",
    ),
)

BARRIER_ARCHIVED_REASON = Choices(
    ("DUPLICATE", "Duplicate"),
    ("NOT_A_BARRIER", "Not a barrier"),
    ("OTHER", "Other"),
)

TRADE_DIRECTION_CHOICES = Choices(
    (1, "Exporting from the UK or investing overseas"),
    (2, "Importing or investing into the UK"),
)

TRADING_BLOCS = {
    "TB00016": {
        "code": "TB00016",
        "name": "European Union (EU)",
        "short_name": "the EU",
        "country_ids": [
            "a05f66a0-5d95-e211-a939-e4115bead28a",  # Austria
            "a75f66a0-5d95-e211-a939-e4115bead28a",  # Belgium
            "57af72a6-5d95-e211-a939-e4115bead28a",  # Bulgaria
            "6caf72a6-5d95-e211-a939-e4115bead28a",  # Croatia
            "6eaf72a6-5d95-e211-a939-e4115bead28a",  # Cyprus
            "6faf72a6-5d95-e211-a939-e4115bead28a",  # Czechia
            "70af72a6-5d95-e211-a939-e4115bead28a",  # Denmark
            "d5f682ac-5d95-e211-a939-e4115bead28a",  # Estonia
            "daf682ac-5d95-e211-a939-e4115bead28a",  # Finland
            "82756b9a-5d95-e211-a939-e4115bead28a",  # France
            "83756b9a-5d95-e211-a939-e4115bead28a",  # Germany
            "e3f682ac-5d95-e211-a939-e4115bead28a",  # Greece
            "6d6a9ab2-5d95-e211-a939-e4115bead28a",  # Hungary
            "736a9ab2-5d95-e211-a939-e4115bead28a",  # Ireland
            "84756b9a-5d95-e211-a939-e4115bead28a",  # Italy
            "806a9ab2-5d95-e211-a939-e4115bead28a",  # Latvia
            "866a9ab2-5d95-e211-a939-e4115bead28a",  # Lithuania
            "876a9ab2-5d95-e211-a939-e4115bead28a",  # Luxembourg
            "0850bdb8-5d95-e211-a939-e4115bead28a",  # Malta
            "1950bdb8-5d95-e211-a939-e4115bead28a",  # Netherlands
            "5361b8be-5d95-e211-a939-e4115bead28a",  # Poland
            "5461b8be-5d95-e211-a939-e4115bead28a",  # Portugal
            "5861b8be-5d95-e211-a939-e4115bead28a",  # Romania
            "200be5c4-5d95-e211-a939-e4115bead28a",  # Slovakia
            "210be5c4-5d95-e211-a939-e4115bead28a",  # Slovenia
            "86756b9a-5d95-e211-a939-e4115bead28a",  # Spain
            "300be5c4-5d95-e211-a939-e4115bead28a",  # Sweden
            "80756b9a-5d95-e211-a939-e4115bead28a",  # United Kingdom
        ],
        "overseas_regions": [
            "3e6809d6-89f6-4590-8458-1d0dab73ad1a",  # Europe
        ],
    },
    "TB00017": {
        "code": "TB00017",
        "name": "Gulf Cooperation Council (GCC)",
        "short_name": "the GCC",
        "country_ids": [
            "a35f66a0-5d95-e211-a939-e4115bead28a",
            "7d6a9ab2-5d95-e211-a939-e4115bead28a",
            "4a61b8be-5d95-e211-a939-e4115bead28a",
            "5661b8be-5d95-e211-a939-e4115bead28a",
            "1a0be5c4-5d95-e211-a939-e4115bead28a",
            "b46ee1ca-5d95-e211-a939-e4115bead28a",
        ],
        "overseas_regions": [
            "c4679b44-079e-4394-8bf7-bb0881a5031d",
        ],
    },
    "TB00013": {
        "code": "TB00013",
        "name": "Eurasian Economic Union (EAEU)",
        "short_name": "the EAEU",
        "country_ids": [
            "9d5f66a0-5d95-e211-a939-e4115bead28a",
            "a65f66a0-5d95-e211-a939-e4115bead28a",
            "786a9ab2-5d95-e211-a939-e4115bead28a",
            "7e6a9ab2-5d95-e211-a939-e4115bead28a",
            "5961b8be-5d95-e211-a939-e4115bead28a",
        ],
        "overseas_regions": ["cb2864aa-d19f-44b6-946c-d850a3fd7e3a"],
    },
    "TB00026": {
        "code": "TB00026",
        "name": "Southern Common Market (Mercosur)",
        "short_name": "the Mercosur",
        "country_ids": [
            "b66ee1ca-5d95-e211-a939-e4115bead28a",
            "b05f66a0-5d95-e211-a939-e4115bead28a",
            "4f61b8be-5d95-e211-a939-e4115bead28a",
            "9c5f66a0-5d95-e211-a939-e4115bead28a",
        ],
        "overseas_regions": [
            "5616ccf5-ab4a-4c2c-9624-13c69be3c46b",
        ],
    },
}


TRADING_BLOC_CHOICES = (
    (trading_bloc["code"], trading_bloc["name"])
    for trading_bloc in TRADING_BLOCS.values()
)


class OrganisationType(StatusNameMixin):
    MINISTERIAL_DEPARTMENTS = 1
    DEVOLVED_ADMINISTRATIONS = 2
    NON_MINISTERIAL_DEPARTMENTS = 3
    AGENCIES_AND_OTHER_PUBLIC_BODIES = 4

    choices = Choices(
        (MINISTERIAL_DEPARTMENTS, "Ministerial departments"),
        (DEVOLVED_ADMINISTRATIONS, "Devolved administrations"),
    )


GOVERNMENT_ORGANISATION_TYPES = (
    OrganisationType.MINISTERIAL_DEPARTMENTS,
    OrganisationType.DEVOLVED_ADMINISTRATIONS,
    OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    OrganisationType.AGENCIES_AND_OTHER_PUBLIC_BODIES,
)


AWAITING_REVIEW_FROM = Choices(
    ("0", "CONTENT", "Content"),
    ("10", "CONTENT_AFTER_CHANGES", "Content (edited since last review)"),
    ("20", "HM_TRADE_COMMISSION", "HM Trade Commission"),
    ("30", "GOVERNMENT_ORGANISATION", "Government organisation"),
)
