#!/bin/bash

# Pillow dependencies
brew install libtiff libjpeg webp little-cms2

# Prepare environment for Scrapy on Mac OSX
xcode-select --install

pip install -r stable-req.txt

./patches/apply_patches.sh
