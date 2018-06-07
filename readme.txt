
django  Backend, data model, DAL, Website
scrapy  Crawler
python 3.6  pyvenv (virtual env)
postgreSQL  
postgreSQL client:   pgAdmin4

root
 |-supersaver       data model, backend and web
 |-crawler          crawler

* Install python 3.6
* Create python virtual environment with python 3.6.
* In project root:
  bin/activate
* pip install -U pip
* pip install -r requirements.txt
* ./setup_mac.sh
* ./supersaver/setup_postgresql_db.sh
* run crawler
  scrapy crawler <crawler name>
