from django.db import models

from uuid import uuid4

from retailer.models import Retailer
from store.models import Store
from category.models import Category, SourceCategory
from common.property import Property


class Product (models.Model):
    """
    Product got special price during promotion date.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    retailer = models.ForeignKey(Retailer, on_delete=models.PROTECT, null=False, related_name='+')
    # Freshchoice and Supervalue can't get product store.
    # A store may have multiple products, a product may also sell in multiple stores.
    stores = models.ManyToManyField(Store, related_name='products')

    title = models.CharField(max_length=256, null=False, blank=False)
    # Product brief decription combine with quantity like 3 packs, 250g, 2kg etc. (freshchoice)
    description = models.CharField(max_length=512, null=False, blank=True, default='')
    price = models.DecimalField(max_digits=11, decimal_places=2)
    # product unit, like each(ea), pack, bag, kg.
    unit = models.CharField(max_length=32, null=False, blank=True, default='')
    saved = models.CharField(max_length=64, null=True, blank=False, default=None)
    landing_page = models.CharField(max_length=512, null=False, blank=False, db_index=True)
    fast_buy_link = models.CharField(max_length=512, null=True, blank=False, db_index=True, default=None)

    promotion_start_date = models.PositiveIntegerField(null=False)
    promotion_end_date = models.PositiveIntegerField(null=False)

    # ready field is used to indicate crawl status, a product is ready only if
    # all of its images are downloaded and processed.
    ready = models.BooleanField(default=False)

    # Foursquare, New World and Pakn Save product can't get category information.
    categories = models.ManyToManyField(Category, related_name='+')
    source_categories = models.ManyToManyField(SourceCategory, related_name='+')
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    active = models.BooleanField(default=True)

    def __repr__(self):
        return 'Product: id={0}, retailer={1}, title={2}, desc={3}, ' \
               'price={4}, unit={5}, saved={6}' \
               'prom_start={7}, prom_end={8},' \
               'detail={9},fast_buy={10}'\
            .format(self.id, self.retailer_id, self.title, self.description,
                    self.price, self.unit, self.saved,
                    self.promotion_start_date, self.promotion_end_date,
                    self.landing_page, self.fast_buy_link)


class ProductProperty (Property):
    """
    Product property bag.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, related_name='properties')

    def __repr__(self):
        return 'ProductProperty: id={0}, name={1}, value={2}, product={3}'.format(
            self.pk, self.name, self.value, self.product_id)


class ProductImage (models.Model):
    """
    Product image
    """
    # Pak'n save product has no image. (a product may have 0 or more images.)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, related_name='product_images')
    unique_hash = models.CharField(max_length=64, unique=True, null=False, blank=False)
    original_url = models.CharField(max_length=512, null=False, blank=False)

    def __repr__(self):
        return 'ProductImage: id={0}, hash={1}, product={2}, origin={3}'.format(
            self.pk, self.unique_hash, self.product_id, self.original_url)
