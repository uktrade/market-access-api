#!/usr/bin/env bash
set -e

POSTGRES="psql --username comtrade_user

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🔥  Dropping API DB                                   "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: comtrade
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
-- Terminate existing connections
REVOKE CONNECT ON DATABASE comtrade FROM public;

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'comtrade';

-- Drop database
DROP DATABASE IF EXISTS comtrade
EOSQL

echo -e "\n"
