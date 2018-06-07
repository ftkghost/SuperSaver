#!/bin/bash
set -e
sudo pg_ctl start -D /usr/local/var/postgres -l logfile

# sudo mysql.server start
# sudo service apache2 stop
sudo service ngnix stop

./manage.py runserver
