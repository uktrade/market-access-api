#!/bin/bash

psql -U comtrade_user -f /db-dumps/db.dump.sql comtrade;

