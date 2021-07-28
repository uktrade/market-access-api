#!/usr/bin/env bash
set -e
DUMPFILE=$1
POSTGRES="psql --username comtrade_user"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🍩  Restoring API DB                                  "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: comtrade                          "
echo -e "  dump: db.dump.sql
echo -e "╚══════════════════════════════════════════════════════╝"

gunzip < /var/lib/comtrade_postgresql/dumps/db.dump.sql | ${POSTGRES} comtrade

echo -e "\n"
