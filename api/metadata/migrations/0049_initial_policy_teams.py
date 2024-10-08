from django.db import migrations


POLICY_TEAMS = [
    {
        "pk": 1,
        "title": "Competition",
        "description": "Competition policy is about making sure UK firms can operate on an equal basis with domestic businesses within a foreign market. This involves making sure that there are adequate anti-trust laws in place to effectively regulate competition. Examples of barriers in this area include anti-competitive collusion and price fixing between firms (cartels), abuse of dominant market monopolies and anti-competitive mergers."
    },
    {
        "pk": 2,
        "title": "Customs",
        "description": "Customs policy concerns the impact of operational procedures and requirements on moving goods before, at, and after the border. Examples of barriers in this area include complex documentation requirements, a lack of information about customs processes, delays in the release of goods or delays at the border, and complex verification processes."
    },
    {
        "pk": 3,
        "title": "Digital and Telecoms",
        "description": "Digital trade policy covers digital transactions for goods and services, which may be digitally or physically delivered. Telecommunications (telecoms) covers exchange of information by electromagnetic means, such as fixed line and mobile telephones or broadband services. For example, digital trade barriers include unjustified restrictions on cross-border data flows, telecoms barriers include limitations on interconnection or access to telecoms infrastructure in a country."
    },
    {
        "pk": 4,
        "title": "Environment and climate",
        "description": "Climate and environment policy includes barriers that may limit the ability of firms to address environmental concerns and enable a global transition to net zero. For example, untransparent procurement processes, inadequate infrastructure, or regulatory framework for the incorporation of renewable technologies. But it can also include excessive environmental stringency which may act as a form of disguised protectionism - such as taxes, trading schemes, penalties or non-market based regulatory controls."
    },
    {
        "pk": 5,
        "title": "Gender",
        "description": "Gender-based barriers to trade can either be gender-specific (barriers which specifically impact women) or gender-intensive ( barriers which disproportionately affect women)."
    },
    {
        "pk": 6,
        "title": "Goods Market Access (GMA)",
        "description": "Goods Market Access (GMA) barriers arise when a country applies tariffs on exports of UK goods which makes UK exporters uncompetitive in that market, or when there’s a Free Trade Agreement (FTA) but a country does not comply with an agreed preferential tariff for the UK.  It can also relate to non-tariff areas such as import and export licensing and import restrictions."
    },
    {
        "pk": 7,
        "title": "Good Regulatory Practice (GRP)",
        "description": "GRP are the best practices and procedures developed by governments and organisations to improve the quality of trade regulation. It aims to reduce regulatory divergence between countries, creating a stable regulatory environment that promotes investor and exporter confidence. GRP principles include transparency through the publication of regulations, public consultations, regulatory impact assessments, retrospective reviews of existing regulatory measures, and regulatory cooperation."
    },
    {
        "pk": 8,
        "title": "Intellectual Property",
        "description": "The UK uses its intellectual property (IP) trade policy to ease access into markets for UK rights holders. Central concerns within the IP space include difficulty acquiring new and protecting existing IP rights (eligibility and maintenance), conditions under which IP rights will no longer be recognised (exhaustion), and a lack of legal procedures to deal with the infringement of IP rights (enforcement). Other issues include forced-technology transfer in exchange for market access and regulations limiting the deployment of brand representation."
    },
    {
        "pk": 9,
        "title": "Investment",
        "description": "Investment policy aims to reduce barriers for UK investors in partner markets, so they can set up and operate overseas.  Investment barriers are mainly discriminatory treatment of foreign investors – through restrictions and requirements. For example, equity caps, joint venture requirements, limitations on movement of capital, and restrictive investment screening processes. However, barriers can also take an administrative nature, for instance a lack of transparent investment regulations, or slow or unfair investment authorisation procedures."
    },
    {
        "pk": 10,
        "title": "Procurement",
        "description": "Public procurement is the process by which governments and public bodies acquire the goods and services that are needed to fulfil various functions such as infrastructure, defence, or healthcare provision. Barriers that could obstruct firms when applying for or fulfilling public procurement contracts include a lack of transparency, preferential treatment for local suppliers, qualification and evaluation criteria, bureaucratic  processes and corruption."
    },
    {
        "pk": 11,
        "title": "Rules of Origin (RoO)",
        "description": "Rules of Origin (RoO) are the regulations and means used by an importing country to determine the country of origin for goods imports which can affect the exporter's eligibility to claim preferential tariff rates. This is defined in terms of where the goods were produced, manufactured or substantially transformed, rather than the last location of shipment. RoO also cover how goods are transported from one trading partner to another. Barriers may include prohibitive complexity and costs in gaining the documentation needed to comply with the RoO, such as a certificate of origin, proof of direct shipment or a packing list."
    },
    {
        "pk": 12,
        "title": "Sanitary and Phytosanitary measures (SPS)",
        "description": "Sanitary and phytosanitary (SPS) policy covers trade in products or services designed to protect human, animal or plant life.  It includes certifying and verifying that live animals, products of animal origin and plant products meet the standards set out between trading partners. Examples of barriers could be when business cannot obtain export health certificates (EHCs), import bans in response to contamination or animal and plant disease transmission concerns, or listing of exporting establishments."
    },
    {
        "pk": 13,
        "title": "Small and Medium Enterprises (SME)",
        "description": "SME trade policy aims to support the SME business community by reducing information barriers and enhancing cooperation with key partners. We support SMEs in international trade by increasing transparency on rules and regulations (reducing informational barriers faced by SMEs), cooperating with trading partners to support SMEs, and securing FTAs that benefit the whole economy, not just large companies."
    },
    {
        "pk": 14,
        "title": "State-owned enterprises",
        "description": "State-owned Enterprises (SOEs) are commercial enterprises over which a government exercises ownership or control. SOE policy seeks to make sure UK private enterprises are not  impacted negatively by SOEs and are able to operate on an equal basis. Examples of barriers SEOs can pose to UK firms include when they act as the primary domestic manufacturer for an industry (monopoly), when they are the sole importer or buyer for a good (monopsony) or when they are responsible for managing a public service, such as the railways."
    },
    {
        "pk": 15,
        "title": "Subsidies",
        "description": "Subsidies policy is concerned with harmful monetary or non-monetary support provided by the partner government that can negatively impact UK firms by granting unfair advantages to domestic providers. For example, the provision of subsidies in a country can reduce the price of domestic goods or services, making UK imports uncompetitive."
    },
    {
        "pk": 16,
        "title": "Technical barriers to trade (TBT)",
        "description": "Technical barriers to trade (TBT) are non-tariff barriers on goods that establish product requirements in areas such as safety, quality, performance, identity and the provision of information to consumers. For example, this could include complex packaging and labelling requirements for alcoholic drink imports which may also favour domestic producers."
    },
    {
        "pk": 17,
        "title": "Trade in services",
        "description": "Services trade relates to transactions of intangible products that are distinct from the production of physical goods. For example, UK touring musicians and those working in the creative industries. Barriers to services trade include market entry restrictions from operating within a specific sector, screening and approval requirements, lack of recognition for professional qualifications, discrimination between foreign and domestic services providers, lack of transparency in visa requirements or other restrictions on the operations and the movement of personnel."
    },
]


def create_policy_teams(apps, schema_editor):
    PolicyTeam = apps.get_model("metadata", "PolicyTeam")

    for policy_team in POLICY_TEAMS:
        try:
            PolicyTeam.objects.get(pk=policy_team["pk"])
        except PolicyTeam.DoesNotExist:
            PolicyTeam.objects.create(**policy_team)


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0048_policyteam_historicalpolicyteam"),
    ]

    operations = [
        migrations.RunPython(create_policy_teams),
    ]
