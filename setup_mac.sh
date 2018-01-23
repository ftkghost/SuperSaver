#!/bin/bash
db_user=supersaver
db_userpwd=supersaver123

# Prepare environment for Scrapy on Mac OSX
xcode-select --install

# Pillow dependencies
brew install libtiff libjpeg webp little-cms2

# * Install mysql
brew install mysql
# Install 
curl -O https://cdn.mysql.com//Downloads/Connector-Python/mysql-connector-python-2.1.7-osx10.12.dmg
# * Install nginx (linux)

pip install -r requirements.txt

./patches/apply_patches.sh


mysql -uroot -p<<EOF
CREATE USER '${db_user}'@'localhost' IDENTIFIED BY '${db_userpwd}';
flush PRIVILEGES;
EOF
