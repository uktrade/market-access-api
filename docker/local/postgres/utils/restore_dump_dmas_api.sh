#!/usr/bin/env bash
set -e
DUMPFILE=$1
POSTGRES="psql --username ${POSTGRES_USER}"

echo -e "╔══════════════════════════════════════════════════════╗"
echo -e "  🍩  Restoring API DB                                  "
echo -e "╠══════════════════════════════════════════════════════╣"
echo -e "  database: ${API_POSTGRES_DB}                          "
echo -e "  dump: ${DUMPFILE}                                     "
echo -e "╚══════════════════════════════════════════════════════╝"

gunzip < /var/lib/postgresql/dumps/${DUMPFILE} | ${POSTGRES} ${API_POSTGRES_DB}

echo -e "\n"
