#!/usr/bin/env bash
set -e

POSTGRES="psql --username comtrade_user"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🧙  ‍Creating API DB                                   "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: comtrade                          "
echo -e "╚══════════════════════════════════════════════════════╝"

${POSTGRES} <<-EOSQL
CREATE DATABASE comtrade OWNER comtrade_user;
EOSQL

echo -e "\n"
