#!/usr/bin/env bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🏗 Creating DB role 🏗                                "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  role: ${PYFE_POSTGRES_USER}                           "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
CREATE USER ${PYFE_POSTGRES_USER} WITH CREATEDB PASSWORD '${PYFE_POSTGRES_PASS}';
EOSQL
