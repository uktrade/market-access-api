FROM postgres:latest

ADD ./init-db.sh /docker-entrypoint-initdb.d/
ADD ./db.dump.sql /db-dumps/
