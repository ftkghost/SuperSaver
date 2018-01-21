# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from .djangoitem3 import DjangoItem

from product.models import Product, ProductProperty
from store.models import Store
from region.models import Region

# Mapping SuperSaver django project model to Scrapy items.


class ProductItem(DjangoItem):
    django_model = Product


class ProductPropertyItem(DjangoItem):
    django_model = ProductProperty


class StoreItem(DjangoItem):
    django_model = Store


class RegionItem(DjangoItem):
    django_model = Region
