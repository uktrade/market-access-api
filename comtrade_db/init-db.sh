#!/bin/bash

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE comtrade;
    GRANT ALL PRIVILEGES ON DATABASE comtrade TO comtrade_user;
EOSQL

psql -f /db-dumps/db.dump.sql comtrade;

