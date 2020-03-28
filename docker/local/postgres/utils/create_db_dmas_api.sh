#!/usr/bin/env bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🧙  ‍Creating API DB                                   "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: ${API_POSTGRES_DB}                          "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
CREATE DATABASE ${API_POSTGRES_DB} OWNER ${POSTGRES_USER};
EOSQL

echo -e "\n"
