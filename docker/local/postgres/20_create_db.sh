#!/usr/bin/env bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🏗 Creating DB 🏗                                     "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: ${PYFE_POSTGRES_DB}                         "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
CREATE DATABASE ${PYFE_POSTGRES_DB} OWNER ${PYFE_POSTGRES_USER};
EOSQL
