#!/bin/bash
db_user=supersaver
db_userpwd=supersaver123

# Prepare environment for Scrapy on Mac OSX
xcode-select --install

# Pillow dependencies
brew install libtiff libjpeg webp little-cms2

# * Install nginx (linux)

# Setup mysql and user
#./setup_mysql_db.sh '${db_user}' '${db_userpwd}'

# Setup postgreSQL and user
./setup_postgresql_db.sh '${db_user}'

pip install -r requirements.txt

./patches/apply_patches.sh
