import traceback
import threading
import logging
from datetime import datetime
import scrapy

from source.models import DataSource
from country.models import Country
from region.models import Region
from product.models import Product
from retailer.models import Retailer

from supersaver.settings import STATIC_URL
from dealcrawler.util import *


def parsing_failure_logging_decorator(desc):
    """
    Decorator to log spider parsing failure in spider class method.
    """
    def _parsing_failure_logging_imp(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except:
                self.log("{0}\nError: {1}".format(desc, traceback.format_exc()))
                raise
        return wrapper
    return _parsing_failure_logging_imp


def parsing_failure_logging_gen_decorator(desc):
    """
    Decorator to log spider parsing failure in spider class method (generator).
    """
    def _parsing_failure_logging_gen_imp(func):
        def wrapper(self, *args, **kwargs):
            try:
                # Must execute generator, otherwise you can't catch the exception
                # from method returns generator.
                for item in func(self, *args, **kwargs):
                    yield item
            except:
                self.log("{0}\nError: {1}".format(desc, traceback.format_exc()))
                raise
        return wrapper
    return _parsing_failure_logging_gen_imp


class BaseSpider (scrapy.Spider):
    """
    Base spider
    """
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'

    def __init__(self, datasource_id, country_code, start_urls, host, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logging_level = logging.DEBUG
        self.start_urls = [start_urls] if isinstance(start_urls, str) else start_urls
        self.default_http_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.8',
            'Host': host,
            'User-Agent': self.user_agent,
        }

        self.datasource = DataSource.objects.get(id=datasource_id)
        self.country = Country.objects.get(country_code=country_code)
        regions = Region.objects.filter(country=self.country, active=True)
        self.region_by_name = {r.name: r for r in regions}

        retailers = self.datasource.retailers.all()
        self.retailer_by_name = {r.name: r for r in retailers}
        now = int(datetime.utcnow().timestamp())

        Product.objects.filter(
            retailer__datasource=self.datasource,
            promotion_end_date__lte=now
        ).update(active=False)

        products = Product.objects.filter(
            retailer__datasource=self.datasource,
            promotion_end_date__gt=now)
        self.product_by_landing_page = {p.landing_page: p for p in products}
        self.data_access_lock = threading.RLock()

    def start_requests(self):
        for url in self.start_urls:
            yield self.create_request(url, self.parse, dont_filter=True)

    def save_product_image(self, response, product, image_url):
        pass

    def _add_or_update_prod(self, prod):
        return self._safe_add_or_update_data(
            self.product_by_landing_page, prod, lambda p: p.landing_page)

    def _get_prod(self, landing_page):
        return self._safe_get_data(self.product_by_landing_page, landing_page)

    def _create_or_update_prod_in_db(self, prod_item, prod_image, stores, properties=None):
        db_prod = self._get_prod(prod_item['landing_page'])
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
        self._add_or_update_prod(db_prod)

        # Update product image
        if prod_image and not db_prod.product_images.filter(original_url=prod_image).exists():
            # TODO: Hash
            unique_hash = str(datetime.utcnow().timestamp())
            db_prod.product_images.create(unique_hash=unique_hash,
                                          original_url=prod_image)
        if stores:
            self._update_prod_stores_in_db(db_prod, stores)
        if properties:
            self._update_prod_props_in_db(db_prod, properties)
        return db_prod

    def _update_prod_stores_in_db(self, db_prod, stores):
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

    def _update_prod_props_in_db(self, db_prod, properties):
        ex_props = list(db_prod.properties.all())
        for prop in properties:
            found = None
            for ex_prop in ex_props:
                if ex_prop.value_equals_to(prop):
                    found = ex_prop
            if not found:
                prop.product = db_prod
                prop.save()
            else:
                ex_props.remove(found)
        for p in ex_props:
            p.delete()

    def _add_or_update_retailer(self, retailer):
        return self._safe_add_or_update_data(self.retailer_by_name, retailer, lambda r: r.name)

    def _get_retailer(self, name):
        return self._safe_get_data(self.retailer_by_name, name.lower())

    def _create_or_update_retailer_in_db(self, retailer_name, logo_url=None, properties=None):
        retailer = self._get_retailer(retailer_name)
        if retailer is None:
            retailer = Retailer()
            retailer.name = retailer_name.lower()
            retailer.display_name = retailer_name
            retailer.logo_url = logo_url
            retailer.datasource = self.datasource
            retailer.country = self.country
            retailer.save()
            self._add_or_update_retailer(retailer)
        if properties:
            self._update_retailer_props_in_db(retailer, properties)
        return retailer

    def _update_retailer_props_in_db(self, retailer, properties):
        ex_props = list(retailer.properties.all())
        for prop in properties:
            found = None
            for ex_prop in ex_props:
                if ex_prop.value_equals_to(prop):
                    found = ex_prop
            if not found:
                prop.retailer = retailer
                prop.save()
            else:
                ex_props.remove(found)
        for p in ex_props:
            p.delete()

    def _safe_add_or_update_data(self, data_dict, data, key_func):
        try:
            self.data_access_lock.acquire()
            data_dict[key_func(data)] = data
        finally:
            self.data_access_lock.release()

    def _safe_get_data(self, data_dict, key):
        try:
            self.data_access_lock.acquire()
            if key in data_dict:
                return data_dict[key]
            else:
                return None
        finally:
            self.data_access_lock.release()

    def create_request(self, url, callback, referer=None, **kwargs):
        headers = self.default_http_headers.copy()
        if referer is not None:
            headers['Referer'] = referer
        return scrapy.http.Request(url, callback=callback, headers=headers, **kwargs)

    def log(self, message, level=logging.DEBUG, **kw):
        if level >= self.logging_level:
            super().log(message, level, **kw)

    def log_debug(self, msg_format, *args, **kwargs):
        msg = msg_format.format(*args, **kwargs)
        return self.log(msg, level=logging.DEBUG)
