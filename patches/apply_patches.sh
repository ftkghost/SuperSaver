#!/bin/bash

# Fix scrapy.http.cookies compatibility issue in python 3.4
cp ./scrapy.http.cookies.py $PROJ_ROOT/lib/python3.4/site-packages/scrapy/http/cookies.py
