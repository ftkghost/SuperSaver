import logging
import traceback
from datetime import datetime

import scrapy

from country.models import Country
from product.models import Product
from region.models import Region
from source.models import DataSource
from .data.product_repository import ProductRepository
from .data.retailer_repository import RetailerRepository


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
    Base spider.
    """
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'

    def __init__(self, start_urls, host, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logging_level = logging.DEBUG
        self.start_urls = [start_urls] if isinstance(start_urls, str) else start_urls
        self.default_http_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.8',
            'Host': host,
            'User-Agent': self.user_agent,
        }

    def start_requests(self):
        for url in self.start_urls:
            yield self.create_request(url, self.parse, dont_filter=True)

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


class DealSpider (BaseSpider):
    """
    Abstract deal spider.
    """

    def __init__(self, datasource_id, country_code, start_urls, host, *args, **kwargs):
        super().__init__(start_urls, host, *args, **kwargs)

        self.datasource = DataSource.objects.get(id=datasource_id)
        self.country = Country.objects.get(country_code=country_code)
        regions = Region.objects.filter(country=self.country, active=True)
        self.region_by_name = {r.name: r for r in regions}

        now = int(datetime.utcnow().timestamp())

        Product.objects.filter(
            retailer__datasource=self.datasource,
            promotion_end_date__lte=now
        ).update(active=False)

        products = Product.objects.filter(
            retailer__datasource=self.datasource,
            promotion_end_date__gt=now)
        self.prod_repo = ProductRepository(products)

        self.retailer_repo = RetailerRepository(self.datasource, self.country)

    def _create_or_update_prod_in_db(self, prod_item, prod_image_url, stores, properties=None):
        self.prod_repo.add_or_update_prod_in_db(prod_item, prod_image_url, stores, properties)

    def _create_or_update_retailer_in_db(self, retailer_name, website=None, logo_url=None, properties=None):
        self.retailer_repo.add_or_update_retailer_in_db(retailer_name, website, logo_url, properties)
