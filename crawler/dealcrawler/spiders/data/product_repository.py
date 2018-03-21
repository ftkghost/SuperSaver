# -*- coding: utf-8 -*-

from datetime import datetime
from dealcrawler.common.repository import Repository
from dealcrawler.util import *
from supersaver.settings import STATIC_URL


class ProductRepository (Repository):

    def __init__(self, products):
        super().__init__(products, lambda p: p.landing_page)

    def add_or_update_prod_in_db(self, prod_item, prod_image_url, stores, properties=None):
        """
        Create or update product (or deal) in database and update repository memory store.

        :param prod_item: a ProductItem for django.

        It includes fields:
        title, description, price, unit, saved, promotion_start_date, promotion_end_date, landing_page, fast_buy_link.

        :param prod_image_url: product image url.
        :param stores: the stores which provide this product.
        :param properties: additional properties of this product.
        :return: a django product instance.
        """
        db_prod = self.get_item(prod_item['landing_page'])
        if db_prod is None:
            db_prod = prod_item.save()
        else:
            db_prod.title = prod_item['title']
            db_prod.description = empty_str_if_not_in(prod_item, 'description')
            db_prod.price = prod_item['price']
            db_prod.unit = empty_str_if_not_in(prod_item, 'unit')
            db_prod.saved = none_if_not_in(prod_item, 'saved')
            db_prod.promotion_start_date = prod_item['promotion_start_date']
            db_prod.promotion_end_date = prod_item['promotion_end_date']
            db_prod.landing_page = prod_item['landing_page']
            db_prod.fast_buy_link = none_if_not_in(prod_item, 'fast_buy_link')
            db_prod.active = True
            db_prod.save()
            # Not safe
            prod_item._instance = db_prod
        self.add_or_update_item(db_prod)

        # Update product images
        if prod_image_url and not db_prod.product_images.filter(original_url=prod_image_url).exists():
            # TODO: Hash
            unique_hash = str(datetime.utcnow().timestamp())
            self.__class__._save_product_image(db_prod, prod_image_url)
            db_prod.product_images.create(unique_hash=unique_hash,
                                          original_url=prod_image_url)
        if stores:
            self.__class__._update_prod_stores_in_db(db_prod, stores)
        if properties:
            self.__class__._update_prod_props_in_db(db_prod, properties)
        return db_prod

    @staticmethod
    def _update_prod_stores_in_db(db_prod, stores):
        ex_stores = list(db_prod.stores.all())
        for store in stores:
            found = None
            for ex_store in ex_stores:
                if ex_store.value_equals_to(store):
                    found = ex_store
            if not found:
                if not store.pk:
                    store.save()
                db_prod.stores.add(store)
            else:
                ex_stores.remove(found)
        for s in ex_stores:
            db_prod.stores.remove(s)

    @staticmethod
    def _update_prod_props_in_db(db_prod, properties):
        ex_props = list(db_prod.properties.all())
        for prop in properties:
            found = None
            for ex_prop in ex_props:
                if ex_prop.name == prop.name:
                    found = ex_prop
                    break
            if not found:
                # Create new props
                prop.product = db_prod
                prop.save()
            else:
                if found.value != prop.value:
                    # Update existing props
                    found.value = prop.value
                    found.save()
                # Remove from pending deletion list
                ex_props.remove(found)
        for p in ex_props:
            p.delete()

    @staticmethod
    def _save_product_image(product, image_url):
        # TODO: Save to Disk or File server.
        pass
