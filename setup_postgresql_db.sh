#!/bin/bash
db_user=$1
db_userpwd=$2
db_host=localhost

# * Install mysql
brew install postgresql

createuser ${db_user} --createdb

psql -U ${db_user} <<EOF
\password ${db_user}
EOF
