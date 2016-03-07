#!/bin/bash
set -e
sudo mysql.server start
sudo service apache2 stop
./manage.py runserver
