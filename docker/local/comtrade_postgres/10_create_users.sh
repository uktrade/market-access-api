#!/usr/bin/env bash
set -e

POSTGRES="psql --username comtrade_user"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🏗 Creating DB role 🏗                                "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  role: comtrade_user                           "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
CREATE USER comtrade_user WITH CREATEDB PASSWORD 'postgres';
EOSQL
