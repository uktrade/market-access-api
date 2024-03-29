CREATE TABLE comtrade__goods (
    classification character varying NOT NULL,
    year smallint NOT NULL,
    period smallint NOT NULL,
    period_desc smallint NOT NULL,
    aggregate_level bigint NOT NULL,
    is_leaf_code boolean,
    trade_flow_code bigint NOT NULL,
    trade_flow character varying NOT NULL,
    reporter_code bigint NOT NULL,
    reporter character varying NOT NULL,
    reporter_iso character varying,
    partner_code bigint NOT NULL,
    partner character varying NOT NULL,
    partner_iso character varying,
    commodity_code character varying NOT NULL,
    commodity character varying NOT NULL,
    quantity_unit_code bigint NOT NULL,
    quantity_unit character varying NOT NULL,
    quantity numeric,
    netweight_kg numeric,
    trade_value_usd numeric
);
