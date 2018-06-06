#!/bin/bash
set -e
dropdb supersaver
createdb supersaver -U supersaver
psql -U supersaver<<EOF
GRANT ALL PRIVILEGES ON DATABASE supersaver TO supersaver;
EOF
./manage.py makemigrations
./manage.py migrate
