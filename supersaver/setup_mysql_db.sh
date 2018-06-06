#!/bin/bash
set -e
mysql -uroot -p<<EOF
DROP DATABASE IF EXISTS supersaver;
CREATE DATABASE supersaver CHARSET=utf8;
GRANT ALL PRIVILEGES ON supersaver.* TO 'supersaver'@'localhost';
FLUSH PRIVILEGES;
EOF
./manage.py makemigrations
./manage.py migrate
