__author__ = 'qinpeng'

import logging
from json import loads as json_loads
from urllib import parse as urlparse
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import random

import scrapy

from retailer.models import Retailer
from category.models import Category
from store.models import Store
from region.models import Region
from product.models import Product, ProductImage

from dealcrawler.util import *
from dealcrawler.model.items import ProductItem, StoreItem, RegionItem


UTC_TO_NZ_TIMEZONE_DELTA = timedelta(seconds=12*3600)


class LasooCoNzDealSpider(scrapy.Spider):

    """
    Crawl deals from lasso.co.nz
    """
    name = 'lasoo.co.nz'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/48.0.2564.97 Safari/537.36',
    custom_settings = {
        'ROBOTSTXT_OBEY': False,

    }

    JSONP_HOST = 'css.lasoomedia2.com.au'
    SVER = 'ikt3z7fsszp9rt201651'
    ORIGIN_URL = 'http://www.lasoo.co.nz/'
    RETAILER_DETAIL_URL_FORMAT = 'http://css.lasoomedia2.com.au/api/catalogue;sver={0};' \
                                 'domain=www.lasoo.co.nz;catalogueids={1}?jsonp={2}'
    RETAILER_DEALS_URL_FORMAT = 'http://css.lasoomedia2.com.au/api/cataloguepage;sver={0};' \
                                'domain=www.lasoo.co.nz;catalogueid={1};allpages=1?jsonp={2}'

    def __init__(self):
        random.seed(datetime.now().timestamp())
        pass

    def start_requests(self):
        yield scrapy.Request(self.__class__.ORIGIN_URL, callback=self.parse)

    def parse(self, response):
        for cat_elem in response.xpath('//ul[contains(@class, "catalogue-list")]/li/div/a'):
            cat_detail_url = response.urljoin(cat_elem.extract_first_value_with_xpath('@href'))
            cat_json_data = cat_elem.extract_first_value_with_xpath('@data')
            data = json_loads(cat_json_data)
            if data['object'] == 'catalogue':
                catalogue_id = data['objectid']
                jsonp_tag = self.__class__._get_random_jsonp_tag()
                reatail_detail_url = self.__class__._get_retailer_detail_url(catalogue_id, jsonp_tag)
                yield scrapy.Request(reatail_detail_url,
                                     callback=self.parse_retailer_details,
                                     headers={
                                         'Accept': '*/*',
                                         'Accept-Language': 'en-US,en;q=0.8',
                                         'Host': self.__class__.JSONP_HOST,
                                         'Referer': cat_detail_url,
                                     },
                                     meta={
                                         'catalogue_id': catalogue_id,
                                         'referer': cat_detail_url,
                                         'jsonp_tag': jsonp_tag,
                                     })
            else:
                self.log("unknown catalogue object ({0}). {1}", cat_detail_url, data)

    @classmethod
    def _get_random_jsonp_tag(cls):
        return 'mf%d' % random.randrange(100000000, 999999999)

    @classmethod
    def _get_retailer_detail_url(cls, catalogue_id, jsonp_tag):
        return cls.RETAILER_DETAIL_URL_FORMAT.format(cls.SVER, catalogue_id, jsonp_tag)

    @classmethod
    def _get_deals_url(cls, catalogue_id, jsonp_tag):
        return cls.RETAILER_DEALS_URL_FORMAT.format(cls.SVER, catalogue_id, jsonp_tag)

    @classmethod
    def _get_jsonp_response_data(cls, response_body, jsonp_tag=None):
        json_raw_data = response_body.decode('utf8')
        if jsonp_tag and isinstance(jsonp_tag, str):
            last_bracket = json_raw_data.rindex(')')
            json_raw_data = json_raw_data[len(jsonp_tag) + 1:last_bracket]
        data = json_loads(json_raw_data)
        return data

    def parse_retailer_details(self, response):
        jsonp_tag = response.meta['jsonp_tag']
        json_data = self.__class__._get_jsonp_response_data(response.body, jsonp_tag)
        catalogues = json_data['catalogues']
        if len(catalogues) == 0:
            return []
        catalogue = catalogues[0]
        start_date = catalogue['startDate']
        end_date = catalogue['expiryDate']
        total_pages = catalogue['numberPages']
        retailer_data = catalogue['retailer']
        yield retailer_data

        deal_url = self.__class__._get_deals_url(response.meta['catalogue_id'], jsonp_tag)
        yield scrapy.Request(deal_url,
                             callback=self.parse_deals,
                             headers={
                                 'Accept': '*/*',
                                 'Accept-Language': 'en-US,en;q=0.8',
                                 'Host': self.__class__.JSONP_HOST,
                                 'Referer': response.meta['referer'],
                             },
                             meta={
                                 'jsonp_tag': jsonp_tag
                             })

    def parse_deals(self, response):
        jsonp_tag = response.meta['jsonp_tag']
        deals_data = self._get_jsonp_response_data(response.body, jsonp_tag)
        for page in deals_data:
            offers = page['offers']
            for offer in offers:
                offer_id = offer['id']
                deal = {}
                deal['id'] = offer['id']
                deal['title'] = offer['title']
                deal['image'] = offer['offerimage']['path']
                deal['landing_page'] = urlparse.urljoin(self.__class__.ORIGIN_URL, offer['landingLink'])
                yield deal
