#!/bin/bash

# Prepare environment for Scrapy on Mac OSX
xcode-select --install

# Pillow dependencies
brew install libtiff libjpeg webp little-cms2

# * Install mysql
brew install mysql
# * Install nginx (linux)

pip install -r requirements.txt

./patches/apply_patches.sh
