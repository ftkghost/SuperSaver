#!/bin/bash
set -e
mysql -uroot -p<<EOF
DROP DATABASE IF EXISTS SuperSaver;
CREATE DATABASE SuperSaver CHARSET=utf8;
GRANT ALL PRIVILEGES ON SuperSaver.* TO 'supersaver'@'localhost';
FLUSH PRIVILEGES;
EOF
./manage.py makemigrations
./manage.py migrate
