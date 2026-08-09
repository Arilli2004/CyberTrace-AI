FROM postgres:15-alpine

COPY ../database/schema.sql /docker-entrypoint-initdb.d/01_schema.sql
COPY ../database/seed.sql /docker-entrypoint-initdb.d/02_seed.sql

EXPOSE 5432
