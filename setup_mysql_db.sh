#!/bin/bash
db_user=$1
db_userpwd=$2
db_host=localhost

# * Install mysql
brew install mysql

# Install mysql connector for python 
curl -O https://cdn.mysql.com//Downloads/Connector-Python/mysql-connector-python-2.1.7-osx10.12.dmg

mysql -uroot -p<<EOF
CREATE USER '${db_user}'@'${dh_host}' IDENTIFIED BY '${db_userpwd}'
flush PRIVILEGES;
EOF
