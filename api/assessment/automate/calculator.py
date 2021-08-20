import datetime
import logging
from typing import List, Optional

from api.assessment.automate.exceptions import CountryYearlyDataNotFound

from .comtrade import ComtradeClient
from .countries import get_comtrade_country_name
from .formatters import percent_range, rca, rca_diff, rca_diff_glob, value_range
from .utils import avgtrade, group_and_average, trade_df, trade_df_ind
from .valid_codes import valid_codes

logger = logging.getLogger(__name__)


class AssessmentCalculator:
    _client = None
    warnings: List[str] = []
    version = "1.01"

    def __init__(self, cache=None):
        self.cache = cache
        self.client = ComtradeClient(cache=self.cache)

    def get_year_range(
        self, country1: str, country2: str, year: Optional[str] = None
    ) -> List[str]:
        use_most_recent: bool = year is None
        if use_most_recent:
            # The most recent year for which annual data may be available on Comtrade
            year = str(datetime.datetime.now().year - 1)

        valid_years: List[str] = self.client.get_valid_years(
            year,
            get_comtrade_country_name(country1),
            get_comtrade_country_name(country2),
        )
        logger.info("valid_years=%s", valid_years)

        if not valid_years:
            raise CountryYearlyDataNotFound("Years with trade data unavailable")

        if not use_most_recent and valid_years[0] != year:
            self.warnings.append(
                f"Your chosen ending year {year} was not available. "
                f"Years {','.join(valid_years)} were downloaded instead."
            )
        return valid_years

    def clean_commodity_codes(self, commodity_codes):
        invalid_codes = set(commodity_codes) - set(valid_codes)
        if invalid_codes:
            self.warnings.append(
                f"The following commodity codes were not valid: {', '.join(invalid_codes)}"
            )
        return list(set(commodity_codes) - invalid_codes)

    def get_short_country_name(self, country):
        return {
            "United Kingdom": "the UK",
        }.get(country, country)

    def calculate(
        self, commodity_codes, product, country1, country2="United Kingdom", year=None
    ):
        self.warnings = []
        commodity_codes = self.clean_commodity_codes(commodity_codes)
        years = self.get_year_range(country1, country2, year)
        num_years = len(years)

        partners = (
            get_comtrade_country_name(country1),
            get_comtrade_country_name(country2),
            "World",
        )

        logger.info(
            "years=%s commodity_codes=%s partners=%s", years, commodity_codes, partners
        )

        logger.info("Fetching data for affected products")
        affected_products_df = self.client.get(
            years=years,
            trade_direction=("imports", "exports"),
            commodity_codes=commodity_codes,
            reporters="All",
            partners=partners,
            tidy=True,
        )

        logger.info("Fetching data for all products")
        all_products_df = self.client.get(
            years=years,
            trade_direction=("imports", "exports"),
            commodity_codes=["TOTAL"],
            reporters="All",
            partners=partners,
            tidy=True,
        )

        relationship_list = (
            ("Import", country2, country1),
            ("Import", "World", country1),
            ("Import", country2),
            ("Import", "World"),
            ("Import", country1),
            ("Export", country1, country2),
            ("Export", country1),
            ("Export", "World", country2),
            ("Export", "World"),
            ("Export", "World", country1),
        )

        logger.info("Calculating values")

        df_ap_avgs = []
        for relationship in relationship_list:
            results = trade_df(relationship, affected_products_df, products=product)
            df_ap_avgs += results

        df_total_avgs = []
        for relationship in relationship_list:
            results = trade_df(relationship, all_products_df, products="Total")
            df_total_avgs += results

        df_ap_avgs_ind = []
        for relationship in relationship_list:
            results = trade_df_ind(relationship, affected_products_df)
            df_ap_avgs_ind += results

        df_total_avgs = group_and_average(
            data=df_total_avgs,
            field="total",
            group_by=("trade_flow", "products", "reporter", "partner"),
            years=years,
        )

        df_avgs = group_and_average(
            data=df_ap_avgs,
            field="total",
            group_by=("trade_flow", "products", "reporter", "partner"),
            years=years,
        )
        df_avgs += df_total_avgs

        df_avgs_ind = group_and_average(
            data=df_ap_avgs_ind,
            field="total",
            group_by=(
                "trade_flow",
                "reporter",
                "partner",
                "commodity_code",
                "products",
            ),
            years=years,
        )
        df_avgs_ind += df_total_avgs

        # CALCULATING THE TRADE DATA FLOW INPUTS THAT ARE USED TO GENERATE MAB METRICS (3-year avg of trade flows)

        # Values from import data

        # 1. Partner country imports of affected products from UK
        partner_from_uk = avgtrade(
            df=affected_products_df,
            reporter_input=country1,
            partner_input=country2,
            direction="Import",
            num_years=num_years,
        )

        # 2. Partner country total goods imports from UK
        partner_from_uk_total = avgtrade(
            df=all_products_df,
            reporter_input=country1,
            partner_input=country2,
            direction="Import",
            num_years=num_years,
        )

        # 3. Partner country imports of affected products from world
        partner_from_world = avgtrade(
            df=affected_products_df,
            reporter_input=country1,
            partner_input="World",
            direction="Import",
            num_years=num_years,
        )

        # 4. Partner country total goods imports from World
        partner_from_world_total = avgtrade(
            df=all_products_df,
            reporter_input=country1,
            partner_input="World",
            direction="Import",
            num_years=num_years,
        )

        # 5. World imports of affected products from UK
        world_from_uk = avgtrade(
            df=affected_products_df,
            partner_input=country2,
            direction="Import",
            num_years=num_years,
        )

        # 6. World total goods imports from UK
        world_from_uk_total = avgtrade(
            df=all_products_df,
            partner_input=country2,
            direction="Import",
            num_years=num_years,
        )

        # 7. World imports of affected products from World
        world_from_world = avgtrade(
            df=affected_products_df,
            partner_input="World",
            direction="Import",
            num_years=num_years,
        )

        # 8. World total goods imports from World
        world_from_world_total = avgtrade(
            df=all_products_df,
            partner_input="World",
            direction="Import",
            num_years=num_years,
        )

        # 9. World imports of affected products from partner country
        world_from_partner = avgtrade(
            df=affected_products_df,
            partner_input=country1,
            direction="Import",
            num_years=num_years,
        )

        # 10. World total goods imports from partner country
        world_from_partner_total = avgtrade(
            df=all_products_df,
            partner_input=country1,
            direction="Import",
            num_years=num_years,
        )

        # Values from export data

        # 1. UK exports of affected products to partner country
        uk_to_partner = avgtrade(
            df=affected_products_df,
            reporter_input=country2,
            partner_input=country1,
            direction="Export",
            num_years=num_years,
        )

        # 2. UK total goods exports to partner country
        uk_to_partner_total = avgtrade(
            df=all_products_df,
            reporter_input=country2,
            partner_input=country1,
            direction="Export",
            num_years=num_years,
        )

        # 3. World exports of affected products to partner country
        world_to_partner = avgtrade(
            df=affected_products_df,
            partner_input=country1,
            direction="Export",
            num_years=num_years,
        )

        # 4. World total goods exports to partner country
        world_to_partner_total = avgtrade(
            df=all_products_df,
            partner_input=country1,
            direction="Export",
            num_years=num_years,
        )

        # 5. UK exports of affected products to the World
        uk_to_world = avgtrade(
            df=affected_products_df,
            reporter_input=country2,
            partner_input="World",
            direction="Export",
            num_years=num_years,
        )

        # 6. UK total goods exports to the World
        uk_to_world_total = avgtrade(
            df=all_products_df,
            reporter_input=country2,
            partner_input="World",
            direction="Export",
            num_years=num_years,
        )

        # 7. World exports of affected products to World
        world_to_world = avgtrade(
            df=affected_products_df,
            partner_input="World",
            direction="Export",
            num_years=num_years,
        )

        # 8. World total goods exports to World
        world_to_world_total = avgtrade(
            df=all_products_df,
            partner_input="World",
            direction="Export",
            num_years=num_years,
        )

        # 9. Partner country exports of affected products to World
        partner_to_world = avgtrade(
            df=affected_products_df,
            reporter_input=country1,
            partner_input="World",
            direction="Export",
            num_years=num_years,
        )

        # 10. Partner country total goods exports to World
        partner_to_world_total = avgtrade(
            df=all_products_df,
            reporter_input=country1,
            partner_input="World",
            direction="Export",
            num_years=num_years,
        )

        # CALCULATING THE METRIC OUTPUTS USED IN THE MAB ASSESSMENT

        # 1. Bilateral RCA (Bilateral position)
        if partner_from_world_total == 0:
            bilateral_rca_imp = 0
        else:
            bilateral_rca_imp = (partner_from_uk / partner_from_world_total) - (
                (partner_from_world * partner_from_uk_total)
                / (partner_from_world_total ** 2)
            )

        if world_to_partner_total == 0:
            bilateral_rca_exp = 0
        else:
            bilateral_rca_exp = (uk_to_partner / world_to_partner_total) - (
                (world_to_partner * uk_to_partner_total) / (world_to_partner_total ** 2)
            )

        bilateral_rca = rca(bilateral_rca_imp, bilateral_rca_exp)

        # 2. UK-Global RCA (Potential position - global baseline)
        if world_from_world_total == 0:
            uk_global_rca_imp = 0
        else:
            uk_global_rca_imp = (world_from_uk / world_from_world_total) - (
                (world_from_uk_total * world_from_world) / (world_from_world_total ** 2)
            )

        if world_to_world_total == 0:
            uk_global_rca_exp = 0
        else:
            uk_global_rca_exp = (uk_to_world / world_to_world_total) - (
                (uk_to_world_total * world_to_world) / (world_to_world_total ** 2)
            )

        uk_global_rca = rca(uk_global_rca_imp, uk_global_rca_exp)

        # RCA Difference (UK Global minus Bilateral)
        rca_diff_imp = uk_global_rca_imp - bilateral_rca_imp
        rca_diff_exp = uk_global_rca_exp - bilateral_rca_exp
        uk_rca_diff = rca_diff(
            import_value=rca_diff_imp,
            export_value=rca_diff_exp,
            country1=country1,
            country2=country2,
        )

        # Trading partner-Global RCA
        if world_from_world_total == 0:
            partner_global_rca_imp = 0
        else:
            partner_global_rca_imp = (world_from_partner / world_from_world_total) - (
                (world_from_partner_total * world_from_world)
                / (world_from_world_total ** 2)
            )

        if world_to_world_total == 0:
            partner_global_rca_exp = 0
        else:
            partner_global_rca_exp = (partner_to_world / world_to_world_total) - (
                (partner_to_world_total * world_to_world) / (world_to_world_total ** 2)
            )

        partner_global_rca = rca(partner_global_rca_imp, partner_global_rca_exp)

        # Global RCA difference (UK minus partner country)
        global_rca_diff_imp = uk_global_rca_imp - partner_global_rca_imp
        global_rca_diff_exp = uk_global_rca_exp - partner_global_rca_exp
        global_rca_diff = rca_diff_glob(
            import_value=global_rca_diff_imp,
            export_value=global_rca_diff_exp,
            country1=country1,
            country2=country2,
        )

        # Size of Import Market of Product
        import_market = value_range(partner_from_world, world_to_partner)

        # Value of UK exports of affected products to World
        uk_exports_world = value_range(world_from_uk, uk_to_world)

        # Value of UK exports of affected products to partner country
        uk_exports_affected = value_range(partner_from_uk, uk_to_partner)

        # UK share of import market
        uk_market_share = percent_range(
            partner_from_uk / partner_from_world if partner_from_world else 0,
            uk_to_partner / world_to_partner if world_to_partner else 0,
            decimal_places=1,
        )

        # Imports of affected products as share of total partner country imports
        product_share_partner_imp = percent_range(
            partner_from_world / partner_from_world_total
            if partner_from_world_total
            else 0,
            world_to_partner / world_to_partner_total if world_to_partner_total else 0,
            decimal_places=2,
        )

        # Value of UK exports of affected goods as share of total UK exports to World
        product_share_uk_exp_w = percent_range(
            world_from_uk / world_from_uk_total if world_from_uk_total else 0,
            uk_to_world / uk_to_world_total if uk_to_world_total else 0,
            decimal_places=2,
        )

        # Value of UK exports of affected goods as share of total UK exports to partner country
        product_share_uk_exp_p = percent_range(
            partner_from_uk / partner_from_uk_total if partner_from_uk_total else 0,
            uk_to_partner / uk_to_partner_total if uk_to_partner_total else 0,
            decimal_places=2,
        )

        assessment_data = {
            "version": self.version,
            "commodity_codes": commodity_codes,
            "product": product,
            "start_year": years[-1],
            "end_year": years[0],
            "years": years,
            "warnings": self.warnings,
            "export_potential": {
                "uk_global_rca": uk_global_rca,
                "bilateral_rca": bilateral_rca,
                "uk_rca_difference": uk_rca_diff,
                "partner_global_rca": partner_global_rca,
                "global_rca_difference": global_rca_diff,
                "import_market_size": f"{import_market} (UK has {uk_market_share})",
                "product_share_partner_import": product_share_partner_imp,
                "uk_exports_world": uk_exports_world,
                "uk_exports_affected": uk_exports_affected,
                "product_share_uk_export_world": product_share_uk_exp_w,
                "product_share_uk_export_partner": product_share_uk_exp_p,
            },
            "calculations": {
                "import": {
                    "bilateral_rca": bilateral_rca_imp,
                    "uk_global_rca": uk_global_rca_imp,
                    "rca_difference": rca_diff_imp,
                    "partner_global_rca": partner_global_rca_imp,
                    "global_rca_difference": global_rca_diff_imp,
                    "partner_from_world": partner_from_world,
                    "world_from_uk": world_from_uk,
                    "partner_from_uk": partner_from_uk,
                    "market_share": (
                        partner_from_uk / world_from_uk if world_from_uk else 0
                    ),
                    "uk_share_of_import_market": (
                        partner_from_uk / partner_from_world
                        if partner_from_world
                        else 0
                    ),
                    "product_share_partner_import": (
                        partner_from_world / partner_from_world_total
                        if partner_from_world_total
                        else 0
                    ),
                    "product_share_uk_export_world": (
                        world_from_uk / world_from_uk_total
                        if world_from_uk_total
                        else 0
                    ),
                    "product_share_uk_export_partner": (
                        partner_from_uk / partner_from_uk_total
                        if partner_from_uk_total
                        else 0
                    ),
                },
                "export": {
                    "bilateral_rca": bilateral_rca_exp,
                    "uk_global_rca": uk_global_rca_exp,
                    "rca_difference": rca_diff_exp,
                    "partner_global_rca": partner_global_rca_exp,
                    "global_rca_difference": global_rca_diff_exp,
                    "partner_from_world": world_to_partner,
                    "world_from_uk": uk_to_world,
                    "partner_from_uk": uk_to_partner,
                    "market_share": (uk_to_partner / uk_to_world if uk_to_world else 0),
                    "uk_share_of_import_market": (
                        uk_to_partner / world_to_partner if world_to_partner else 0
                    ),
                    "product_share_partner_import": (
                        world_to_partner / world_to_partner_total
                        if world_to_partner_total
                        else 0
                    ),
                    "product_share_uk_export_world": (
                        uk_to_world / uk_to_world_total if uk_to_world_total else 0
                    ),
                    "product_share_uk_export_partner": (
                        uk_to_partner / uk_to_partner_total
                        if uk_to_partner_total
                        else 0
                    ),
                },
            },
            "aggregate_data": df_avgs,
            "raw_data": df_avgs_ind,
        }
        return assessment_data
