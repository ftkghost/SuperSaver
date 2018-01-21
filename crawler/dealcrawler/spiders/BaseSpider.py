import traceback
import threading
import logging
from datetime import datetime
import scrapy

from source.models import DataSource
from country.models import Country
from region.models import Region
from product.models import Product

from supersaver.settings import STATIC_URL


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
        super(BaseSpider, self).__init__(*args, **kwargs)
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

    def _add_or_update_retailer(self, retailer):
        return self._safe_add_or_update_data(self.retailer_by_name, retailer, lambda r: r.name)

    def _get_retailer(self, name):
        return self._safe_get_data(self.retailer_by_name, name.lower())

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

    def log_debug(self, msgformat, *args, **kwargs):
        msg = msgformat.format(*args, **kwargs)
        return self.log(msg, level=logging.DEBUG)
