#!/bin/bash
db_user=$1
db_userpwd=$2
db_host=localhost

# * Install mysql
brew install postgresql

pg_ctl start -D /usr/local/var/postgres -l logfile

# Create a DB user with 'CREATEDB' attribute/permission.
createuser ${db_user} --createdb

# Set password for new user, you will be prompted to enter password
psql postgres<<EOF
\password ${db_user}
EOF

# Activate extensions for text search
psql postgres<<EOF
CREATE EXTENSION IF NOT EXISTS btree_gin WITH SCHEMA pg_catalog;
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA pg_catalog;
CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA pg_catalog;
EOF
