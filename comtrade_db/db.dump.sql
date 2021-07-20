--
-- PostgreSQL database dump
--

-- Dumped from database version 10.15
-- Dumped by pg_dump version 13.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE comtrade;
--
-- Name: comtrade; Type: DATABASE; Schema: -; Owner: comtrade_user
--

CREATE DATABASE comtrade WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'en_US.UTF-8';


ALTER DATABASE comtrade OWNER TO "comtrade_user";

\connect comtrade

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: un; Type: SCHEMA; Schema: -; Owner: comtrade_manager
--

CREATE SCHEMA un;


ALTER SCHEMA un OWNER TO comtrade_manager;

SET default_tablespace = '';

--
-- Name: comtrade__goods; Type: TABLE; Schema: un; Owner: comtrade_manager
--

CREATE TABLE un.comtrade__goods (
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


ALTER TABLE un.comtrade__goods OWNER TO comtrade_manager;

--
-- Name: comtrade__services; Type: TABLE; Schema: un; Owner: comtrade_manager
--

CREATE TABLE un.comtrade__services (
    id integer NOT NULL,
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
    trade_value_usd numeric
);


ALTER TABLE un.comtrade__services OWNER TO comtrade_manager;

--
-- Name: comtrade__services_20210612t010000_id_seq; Type: SEQUENCE; Schema: un; Owner: comtrade_manager
--

CREATE SEQUENCE un.comtrade__services_20210612t010000_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE un.comtrade__services_20210612t010000_id_seq OWNER TO comtrade_manager;

--
-- Name: comtrade__services_20210612t010000_id_seq; Type: SEQUENCE OWNED BY; Schema: un; Owner: comtrade_manager
--

ALTER SEQUENCE un.comtrade__services_20210612t010000_id_seq OWNED BY un.comtrade__services.id;


--
-- Name: comtrade__services id; Type: DEFAULT; Schema: un; Owner: comtrade_manager
--

ALTER TABLE ONLY un.comtrade__services ALTER COLUMN id SET DEFAULT nextval('un.comtrade__services_20210612t010000_id_seq'::regclass);


--
-- Name: comtrade__services comtrade__services_20210612t010000_pkey; Type: CONSTRAINT; Schema: un; Owner: comtrade_manager
--

ALTER TABLE ONLY un.comtrade__services
    ADD CONSTRAINT comtrade__services_20210612t010000_pkey PRIMARY KEY (id);


--
-- Name: 20210424T010000_01e619633306a249f7e8e85eadfa8604_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_01e619633306a249f7e8e85eadfa8604_idx" ON un.comtrade__goods USING btree (commodity_code, partner_code);


--
-- Name: 20210424T010000_415c9a60f5d0632704fe313ffdda2dc2_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_415c9a60f5d0632704fe313ffdda2dc2_idx" ON un.comtrade__goods USING btree (partner_iso, reporter_iso);


--
-- Name: 20210424T010000_4516f30e6f3772ea14b139c708c5ee5c_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_4516f30e6f3772ea14b139c708c5ee5c_idx" ON un.comtrade__goods USING btree (commodity_code, partner_iso);


--
-- Name: 20210424T010000_4c99f6c8ded784647ad142b35ce546f4_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_4c99f6c8ded784647ad142b35ce546f4_idx" ON un.comtrade__goods USING btree (commodity_code, reporter_iso);


--
-- Name: 20210424T010000_6aad974771862fd10e2bfea8088af58f_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_6aad974771862fd10e2bfea8088af58f_idx" ON un.comtrade__goods USING btree (partner_code, reporter_code);


--
-- Name: 20210424T010000_79c1d5ee8fe5e9580556fdcefb7d241d_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_79c1d5ee8fe5e9580556fdcefb7d241d_idx" ON un.comtrade__goods USING btree (commodity_code, reporter_code);


--
-- Name: 20210424T010000_8900b16c92869a1e65c8de0e3169089f_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_8900b16c92869a1e65c8de0e3169089f_idx" ON un.comtrade__goods USING btree (period, commodity_code);


--
-- Name: 20210424T010000_a42a54fe7743467db2630e4731996a8f_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_a42a54fe7743467db2630e4731996a8f_idx" ON un.comtrade__goods USING btree (period_desc, commodity_code);


--
-- Name: 20210424T010000_a7de0e7980e2593a0e8a81bf4d1cd7dd_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_a7de0e7980e2593a0e8a81bf4d1cd7dd_idx" ON un.comtrade__goods USING btree (reporter_code, partner_code);


--
-- Name: 20210424T010000_b29399b526d646f70fb1839e1a8c83c3_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_b29399b526d646f70fb1839e1a8c83c3_idx" ON un.comtrade__goods USING btree (reporter_iso, reporter_iso);


--
-- Name: 20210424T010000_ec58052c1c53677683ba21e70da145ab_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210424T010000_ec58052c1c53677683ba21e70da145ab_idx" ON un.comtrade__goods USING btree (year, commodity_code);


--
-- Name: 20210612T010000_05fd1630b12b4704e6b3084c223dea12_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_05fd1630b12b4704e6b3084c223dea12_idx" ON un.comtrade__services USING btree (partner_iso, reporter_iso);


--
-- Name: 20210612T010000_159952fcee4d08e281e064ff276336d5_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_159952fcee4d08e281e064ff276336d5_idx" ON un.comtrade__services USING btree (commodity_code, reporter_code);


--
-- Name: 20210612T010000_2801c8ca1fbfbba314f372c951ada5bb_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_2801c8ca1fbfbba314f372c951ada5bb_idx" ON un.comtrade__services USING btree (period, commodity_code);


--
-- Name: 20210612T010000_3d798f7324216ac6d0dc2b3e035a821f_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_3d798f7324216ac6d0dc2b3e035a821f_idx" ON un.comtrade__services USING btree (commodity_code, partner_code);


--
-- Name: 20210612T010000_48aa1a9dae5d3c2f90587475912f0d08_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_48aa1a9dae5d3c2f90587475912f0d08_idx" ON un.comtrade__services USING btree (reporter_iso, reporter_iso);


--
-- Name: 20210612T010000_58a3a984b877fc013aae9641ac19ea89_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_58a3a984b877fc013aae9641ac19ea89_idx" ON un.comtrade__services USING btree (period_desc, commodity_code);


--
-- Name: 20210612T010000_630b98595ae76616f2355c70a82b8e2e_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_630b98595ae76616f2355c70a82b8e2e_idx" ON un.comtrade__services USING btree (reporter_code, partner_code);


--
-- Name: 20210612T010000_a24192ca64244f739b4458a68b228ea0_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_a24192ca64244f739b4458a68b228ea0_idx" ON un.comtrade__services USING btree (partner_code, reporter_code);


--
-- Name: 20210612T010000_aa93cef8ed74d1b733fd2937aaebe80a_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_aa93cef8ed74d1b733fd2937aaebe80a_idx" ON un.comtrade__services USING btree (commodity_code, reporter_iso);


--
-- Name: 20210612T010000_aed59034590e0649805b22977673a7c2_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_aed59034590e0649805b22977673a7c2_idx" ON un.comtrade__services USING btree (commodity_code, partner_iso);


--
-- Name: 20210612T010000_d12dfab17b9754aacd12c5327329a5d6_idx; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX "20210612T010000_d12dfab17b9754aacd12c5327329a5d6_idx" ON un.comtrade__services USING btree (year, commodity_code);


--
-- Name: ix_un_comtrade__services_20210612t010000_aggregate_level; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_aggregate_level ON un.comtrade__services USING btree (aggregate_level);


--
-- Name: ix_un_comtrade__services_20210612t010000_classification; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_classification ON un.comtrade__services USING btree (classification);


--
-- Name: ix_un_comtrade__services_20210612t010000_partner_code; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_partner_code ON un.comtrade__services USING btree (partner_code);


--
-- Name: ix_un_comtrade__services_20210612t010000_period; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_period ON un.comtrade__services USING btree (period);


--
-- Name: ix_un_comtrade__services_20210612t010000_period_desc; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_period_desc ON un.comtrade__services USING btree (period_desc);


--
-- Name: ix_un_comtrade__services_20210612t010000_reporter_code; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_reporter_code ON un.comtrade__services USING btree (reporter_code);


--
-- Name: ix_un_comtrade__services_20210612t010000_year; Type: INDEX; Schema: un; Owner: comtrade_manager
--

CREATE INDEX ix_un_comtrade__services_20210612t010000_year ON un.comtrade__services USING btree (year);


--
-- Name: DATABASE comtrade; Type: ACL; Schema: -; Owner: comtrade_user
--

GRANT ALL ON DATABASE comtrade TO comtrade_manager;


--
-- Name: SCHEMA un; Type: ACL; Schema: -; Owner: comtrade_manager
--

GRANT USAGE ON SCHEMA un TO comtrade_reader;
GRANT USAGE ON SCHEMA un TO market_access_dev;


--
-- Name: TABLE comtrade__goods; Type: ACL; Schema: un; Owner: comtrade_manager
--

GRANT SELECT ON TABLE un.comtrade__goods TO comtrade_reader;
GRANT SELECT ON TABLE un.comtrade__goods TO market_access_dev;


--
-- Name: TABLE comtrade__services; Type: ACL; Schema: un; Owner: comtrade_manager
--

GRANT SELECT ON TABLE un.comtrade__services TO comtrade_reader;
GRANT SELECT ON TABLE un.comtrade__services TO market_access_dev;


--
-- Name: SEQUENCE comtrade__services_20210612t010000_id_seq; Type: ACL; Schema: un; Owner: comtrade_manager
--

GRANT SELECT ON SEQUENCE un.comtrade__services_20210612t010000_id_seq TO comtrade_reader;


--
-- PostgreSQL database dump complete
--

