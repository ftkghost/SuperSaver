#!/bin/bash

# Fix scrapy.http.cookies compatibility issue in python 3.6
cp ./scrapy.http.cookies.py $PROJ_ROOT/lib/python3.6/site-packages/scrapy/http/cookies.py
