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
        (OPEN_PENDING, "Open"),
        (OPEN_IN_PROGRESS, "Open"),
        (RESOLVED_IN_PART, "Resolved: In part"),
        (RESOLVED_IN_FULL, "Resolved: In full"),
        (DORMANT, "Dormant"),
        (ARCHIVED, "Archived"),
        (UNKNOWN, "Unknown"),
    )


class PublicBarrierStatus(StatusNameMixin):

    UNKNOWN = 0
    NOT_ALLOWED = 10
    ALLOWED = 20
    APPROVAL_PENDING = 70
    PUBLISHING_PENDING = 30
    PUBLISHED = 40
    UNPUBLISHED = 50
    REVIEW_LATER = 60

    choices = Choices(
        (UNKNOWN, "Unknown"),
        (NOT_ALLOWED, "Not allowed"),
        (ALLOWED, "Allowed"),
        (APPROVAL_PENDING, "Awaiting approval"),
        (PUBLISHING_PENDING, "Awaiting publishing"),
        (PUBLISHED, "Published"),
        (UNPUBLISHED, "Unpublished"),
        (REVIEW_LATER, "Review later (Depricated)"),
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
    (1, "1: £ thousands"),
    (2, "2: £ tens of thousands"),
    (3, "3: £ hundreds of thousands (£100k - £999k)"),
    (4, "4: £ low hundreds of thousands (£100k-£400k)"),
    (5, "5: £ mid hundreds of thousands (£400k-£700k)"),
    (6, "6: £ high hundreds of thousands (£700k-£999k)"),
    (7, "7: £ millions (£1m-£9.9m)"),
    (8, "8: £ low millions (£1m-£4m)"),
    (9, "9: £ mid millions (£4m-£7m)"),
    (10, "10: £ high millions (£7m-£9.9m)"),
    (11, "11: £ tens of millions (£10m-£99m)"),
    (12, "12: £ low tens of millions (£10m-£40m)"),
    (13, "13: £ mid tens of millions (£40m-£70m)"),
    (14, "14: £ high tens of millions (£70m-£99m)"),
    (15, "15: £ hundreds of millions (£100m-£999m)"),
    (16, "16: £ low hundreds of millions (£100m-£400m)"),
    (17, "17: £ mid hundreds of millions (£400m-£700m)"),
    (18, "18: £ high hundreds of millions (£700m-£999m)"),
    (19, "19: £ billions (£1bn-£9.9bn)"),
    (20, "20: £ low billions (£1bn-£4bn)"),
    (21, "21: £ mid billions (£4bn-£7bn)"),
    (22, "22: £ high billions (£7bn-£9.9bn)"),
    (23, "23: £ tens of billions (£10bn-£20bn)"),
    (24, "24: £ low tens of billions (£10bn-£15bn)"),
    (25, "25: £ high tens of billions (£15bn-£20bn)"),
)

ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS = Choices(
    (1, "£5,000"),
    (2, "£55,000"),
    (3, "£550,000"),
    (4, "£250,000"),
    (5, "£550,000"),
    (6, "£850,000"),
    (7, "£5,500,000"),
    (8, "£2,500,000"),
    (9, "£5,500,000"),
    (10, "£8,500,000"),
    (11, "£55,000,000"),
    (12, "£25,000,000"),
    (13, "£55,000,000"),
    (14, "£85,000,000"),
    (15, "£550,000,000"),
    (16, "£250,000,000"),
    (17, "£550,000,000"),
    (18, "£850,000,000"),
    (19, "£5,500,000,000"),
    (20, "£2,500,000,000"),
    (21, "£5,500,000,000"),
    (22, "£8,500,000,000"),
    (23, "£15,000,000,000"),
    (24, "£12,500,000,000"),
    (25, "£17,500,000,000"),
)

ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC = {
    "£5,000": 5000,
    "£55,000": 55000,
    "£550,000": 550000,
    "£250,000": 250000,
    "£850,000": 850000,
    "£5,500,000": 5500000,
    "£2,500,000": 2500000,
    "£8,500,000": 8500000,
    "£55,000,000": 55000000,
    "£25,000,000": 25000000,
    "£85,000,000": 85000000,
    "£550,000,000": 550000000,
    "£250,000,000": 250000000,
    "£850,000,000": 850000000,
    "£5,500,000,000": 5500000000,
    "£2,500,000,000": 2500000000,
    "£8,500,000,000": 8500000000,
    "£15,000,000,000": 15000000000,
    "£12,500,000,000": 12500000000,
    "£17,500,000,000": 17500000000,
}

ECONOMIC_ASSESSMENT_IMPACT_MIDPOINTS_NUMERIC_LOOKUP = Choices(
    (1, 5000),
    (2, 55000),
    (3, 550000),
    (4, 250000),
    (5, 550000),
    (6, 850000),
    (7, 5500000),
    (8, 2500000),
    (9, 5500000),
    (10, 8500000),
    (11, 55000000),
    (12, 25000000),
    (13, 55000000),
    (14, 85000000),
    (15, 550000000),
    (16, 250000000),
    (17, 550000000),
    (18, 850000000),
    (19, 5500000000),
    (20, 2500000000),
    (21, 5500000000),
    (22, 8500000000),
    (23, 15000000000),
    (24, 12500000000),
    (25, 17500000000),
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
    "TB00003": {
        "code": "TB00003",
        "name": "Association of Southeast Asian Nations (ASEAN)",
        "short_name": "the ASEAN",
        "regional_name": "Asia Pacific",
        "country_ids": [
            "56af72a6-5d95-e211-a939-e4115bead28a",  # Brunei
            "5baf72a6-5d95-e211-a939-e4115bead28a",  # Cambodia
            "706a9ab2-5d95-e211-a939-e4115bead28a",  # Indonesia
            "7f6a9ab2-5d95-e211-a939-e4115bead28a",  # Laos
            "0550bdb8-5d95-e211-a939-e4115bead28a",  # Malaysia
            "59af72a6-5d95-e211-a939-e4115bead28a",  # Myanmar
            "5161b8be-5d95-e211-a939-e4115bead28a",  # Philippines
            "1f0be5c4-5d95-e211-a939-e4115bead28a",  # Singapore
            "a86ee1ca-5d95-e211-a939-e4115bead28a",  # Thailand
            "ba6ee1ca-5d95-e211-a939-e4115bead28a",  # Vietnam
        ],
        "overseas_regions": ["04a7cff0-03dd-4677-aa3c-12dd8426f0d7"],  # Asia Pacific
    },
    "TB00016": {
        "code": "TB00016",
        "name": "European Union (EU)",
        "short_name": "the EU",
        "regional_name": "Europe",
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
        "regional_name": "Middle East, Afghanistan and Pakistan",
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
        "regional_name": "Eastern Europe and Central Asia",
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
        "regional_name": "Latin America",
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


TOP_PRIORITY_BARRIER_STATUS = Choices(
    ("NONE", ""),
    ("APPROVAL_PENDING", "Top 100 Approval Pending"),
    ("REMOVAL_PENDING", "Top 100 Removal Pending"),
    ("APPROVED", "Top 100 Priority"),
    ("RESOLVED", "Top 100 Priority Resolved"),
)

REGIONS_WITH_LEADS = {
    "Latin America": "Regional Lead - LATAC",
    "Asia Pacific": "Regional Lead - APAC",
    "China and Hong Kong": "Regional Lead - China/Hong Kong",
    "South Asia": "Regional Lead - South Asia",
    "Eastern Europe and Central Asia": "Regional Lead - EECAN",
    "Middle East, Afghanistan and Pakistan": "Regional Lead - MEAP",
    "Africa": "Regional Lead - Africa",
    "North America": "Regional Lead - North America",
    "Europe": "Regional Lead - Europe",
    "Wider Europe": "Regional Lead - Wider Europe",
}

WIDER_EUROPE_REGIONS = {
    "Switzerland",
    "Iceland",
    "Norway",
    "Liechtenstein",
    "Israel",
    "Albania",
    "Montenegro",
    "North Macedonia",
    "Serbia",
    "Bosnia and Herzegovina",
    "Kosovo",
    "Greenland",
    "Faroe Islands",
    "Occupied Palestinian Territories",
}

BARRIER_SEARCH_ORDERING_CHOICES = {
    "-reported": {
        "ordering": "-reported_on",
        "label": "Date reported (newest)",
        "order_on": "reported_on",
        "direction": "descending",
    },
    "reported": {
        "ordering": "reported_on",
        "label": "Date reported (oldest)",
        "order_on": "reported_on",
        "direction": "ascending",
    },
    "-updated": {
        "ordering": "-modified_on",
        "label": "Last updated (most recent)",
        "order_on": "modified_on",
        "direction": "descending",
    },
    "updated": {
        "ordering": "modified_on",
        "label": "Last updated (least recent)",
        "order_on": "modified_on",
        "direction": "ascending",
    },
    "-value": {
        "ordering": "-valuation_assessments__impact",
        "ordering-filter": {"valuation_assessments__archived": True},
        "label": "Value (highest)",
        "order_on": "valuation_assessments__impact",
        "direction": "descending",
    },
    "value": {
        "ordering": "valuation_assessments__impact",
        "ordering-filter": {"valuation_assessments__archived": True},
        "label": "Value (lowest)",
        "order_on": "valuation_assessments__impact",
        "direction": "ascending",
    },
    "-resolution": {
        "ordering": "-estimated_resolution_date",
        "label": "Estimated resolution date (most recent)",
        "order_on": "estimated_resolution_date",
        "direction": "descending",
    },
    "resolution": {
        "ordering": "estimated_resolution_date",
        "label": "Estimated resolution date (least recent)",
        "order_on": "estimated_resolution_date",
        "direction": "ascending",
    },
    "-resolved": {
        "ordering": "-status_date",
        "ordering-filter": {"status": BarrierStatus.RESOLVED_IN_FULL},
        "label": "Date resolved (most recent)",
        "order_on": "status_date",
        "direction": "descending",
    },
    "resolved": {
        "ordering": "status_date",
        "ordering-filter": {"status": BarrierStatus.RESOLVED_IN_FULL},
        "label": "Date resolved (least recent)",
        "order_on": "status_date",
        "direction": "ascending",
    },
    "relevance": {
        "ordering": "relevance",
        "ordering-filter": "query_calculated",
        "label": "Relevence to the search term",
        "order_on": "similarity",
        "direction": "descending",
    },
}

FEEDBACK_FORM_SATISFACTION_ANSWERS = Choices(
    ("NONE", ""),
    ("VERY_SATISFIED", "Very satisfied"),
    ("SATISFIED", "Satisfied"),
    ("NEITHER", "Neither satisfied nor dissatisfied"),
    ("DISSATISFIED", "Dissatisfied"),
    ("VERY_DISSATISFIED", "Very dissatisfied"),
)

FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS = Choices(
    ("REPORT_BARRIER", "Report a barrier"),
    ("PROGRESS_UPDATE", "Set a progress update"),
    ("EXPORT_BARRIER_CSV", "Export a barrier CSV report"),
    ("ACTION_PLAN", "Create or edit an action plan"),
    ("OTHER", "Other"),
    ("DONT_KNOW", "Don't know"),
)

FEEDBACK_FORM_EXPERIENCED_ISSUES_ANSWERS = Choices(
    ("NO_ISSUE", "I did not experience any issues"),
    ("UNABLE_TO_FIND", "I did not find what I was looking for"),
    ("DIFFICULT_TO_NAVIGATE", "I found it difficult to navigate"),
    ("LACKS_FEATURE", "The system lacks the feature I need"),
    ("OTHER", "Other"),
)

PRIORITY_LEVELS = Choices(
    ("NONE", ""),
    ("OVERSEAS", "Overseas Delivery"),
    ("REGIONAL", "Regional Priority"),
    ("COUNTRY", "Country Priority"),
    ("WATCHLIST", "Watch list"),
)

NEXT_STEPS_ITEMS_STATUS_CHOICES = Choices(
    ("NOT_STARTED", "Not started"),
    ("IN_PROGRESS", "In progress"),
    ("COMPLETED", "Completed"),
)
