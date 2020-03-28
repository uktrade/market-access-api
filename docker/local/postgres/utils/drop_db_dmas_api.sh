#!/usr/bin/env bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🔥  Dropping API DB                                   "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: ${API_POSTGRES_DB}                          "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
-- Terminate existing connections
REVOKE CONNECT ON DATABASE ${API_POSTGRES_DB} FROM public;

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${API_POSTGRES_DB}';

-- Drop database
DROP DATABASE IF EXISTS ${API_POSTGRES_DB}
EOSQL

echo -e "\n"
