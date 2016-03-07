#!/bin/bash
set -e
mysql -uroot -p<<EOF
drop database if exists SuperSaver;
create database SuperSaver charset=utf8;
GRANT ALL PRIVILEGES on SuperSaver.* to 'supersaver'@'localhost';
flush PRIVILEGES;
EOF
./manage.py makemigrations
./manage.py migrate
