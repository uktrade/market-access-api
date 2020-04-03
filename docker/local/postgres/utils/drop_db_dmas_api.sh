#!/usr/bin/env bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🔥  Dropping API DB                                   "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: ${API_POSTGRES_DB}                          "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
-- Making sure the database exists
-- SELECT * FROM pg_database WHERE datname = ${API_POSTGRES_DB}

-- Disallow new connections
-- UPDATE pg_database SET datallowconn = 'false' WHERE datname = ${API_POSTGRES_DB};
-- ALTER DATABASE ${API_POSTGRES_DB} CONNECTION LIMIT 1;

-- Terminate existing connections
-- SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = ${API_POSTGRES_DB};

-- Drop database
DROP DATABASE ${API_POSTGRES_DB}
EOSQL

echo -e "\n"
