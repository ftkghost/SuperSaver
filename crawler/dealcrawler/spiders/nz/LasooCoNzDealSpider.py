__author__ = 'qinpeng'

import logging
from json import loads as json_loads
from urllib import parse as urlparse
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import random

import scrapy
from supersaver.settings import make_internal_property_name

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

    SVER = 'ikt3z7fsszp9rt201651'
    ORIGIN_URL = 'https://www.lasoo.co.nz/'

    JSONP_HOST = 'www.lasoo.co.nz'
    RETAILER_INFO_URL_FORMAT = 'https://www.lasoo.co.nz/data.js?type=catalogue' \
                               '&catalogueids={0}&jsonp={1}'
    RETAILER_DEALS_URL_FORMAT = 'https://www.lasoo.co.nz/data.js?type=cataloguepage' \
                                '&catalogueid={0}&allpages=1&jsonp={1}'
    OFFER_DETAILS_URL_FORMAT = 'https://www.lasoo.co.nz/data.js?type=offer&id={0}&jsonp={1}'

    def __init__(self):
        random.seed(datetime.now().timestamp())
        pass

    def start_requests(self):
        yield scrapy.Request(self.__class__.ORIGIN_URL, callback=self.parse)

    def parse(self, response):
        for cat_elem in response.xpath('//ul[contains(@class, "catalogue-list")]/li/div/a'):
            cat_detail_url = response.urljoin(extract_first_value_with_xpath(cat_elem, '@href'))
            cat_json_data = extract_first_value_with_xpath(cat_elem, '@data')
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
        return cls.RETAILER_INFO_URL_FORMAT.format(catalogue_id, jsonp_tag)

    @classmethod
    def _get_deals_url(cls, catalogue_id, jsonp_tag):
        return cls.RETAILER_DEALS_URL_FORMAT.format(catalogue_id, jsonp_tag)

    @classmethod
    def _get_offer_url(cls, offer_id, jsonp_tag):
        return cls.OFFER_DETAILS_URL_FORMAT.format(offer_id, jsonp_tag)

    @classmethod
    def _get_jsonp_response_data(cls, response_body, jsonp_tag=None):
        json_raw_data = response_body.decode('utf8')
        if jsonp_tag and isinstance(jsonp_tag, str):
            last_bracket = json_raw_data.rindex(')')
            json_raw_data = json_raw_data[len(jsonp_tag) + 1:last_bracket]
        data = json_loads(json_raw_data)
        return data

    @classmethod
    def _get_http_headers(cls, referer):
        return {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.8',
            'Host': cls.JSONP_HOST,
            'Referer': referer,
        }

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
        retailer = {
            'name': retailer_data['name'],
            'display_name': retailer_data['name'],
            'logo_url': retailer_data['smallImage'],
            'country': self.country,
            'datasource': self.datasource,
            'properties': [
                {
                    'name': make_internal_property_name('lasso_retailer_id'),
                    'value': retailer_data['id'],
                },
                {
                    'name': make_internal_property_name('lasso_unique_name'),
                    'value': retailer_data['uniqueName'],
                },
                {
                    'name': make_internal_property_name('lasso_code'),
                    'value': retailer_data['code'],
                }

            ]
        }

        yield retailer_data
        # Update jsonp for new request
        jsonp_tag = self.__class__._get_random_jsonp_tag()
        deal_url = self.__class__._get_deals_url(response.meta['catalogue_id'], jsonp_tag)
        meta = response.meta
        meta['start_date'] = start_date
        meta['end_date'] = end_date
        meta['retailer'] = retailer
        meta['jsonp_tag'] = jsonp_tag
        yield scrapy.Request(deal_url,
                             callback=self.parse_deals,
                             headers=self.__class__._get_http_headers(meta['referer']),
                             meta=meta)

    def parse_deals(self, response):
        jsonp_tag = response.meta['jsonp_tag']
        deals_data = self._get_jsonp_response_data(response.body, jsonp_tag)

        meta = response.meta
        # Update jsonp for new request
        jsonp_tag = self.__class__._get_random_jsonp_tag()
        meta['jsonp_tag'] = jsonp_tag


        # if 'categoryPath' in offer:
        #     cats = offer['categoryPath']
        #     for c in cats:
        #         category = SourceCategory()
        #         c.name = c['uniqueName']
        #         c.source_category_id = c['id']
        #         c.display_name = c['name']
        #         c.source = self.datasource
        #         c.save()


        for page in deals_data:
            offers = page['offers']
            if offers is None:
                continue
            for offer in offers:
                if offer['type'] != 'offer':
                    continue
                deal = {}
                deal['id'] = offer['id']
                deal['title'] = offer['title']
                if 'offerimage' in offer:
                    deal['image'] = offer['offerimage']['path']
                deal['landing_page'] = response.urljoin(offer['landingLink'])

                meta['offer'] = deal
                meta['referer'] = response.url
                offer_json_url = self.__class__._get_offer_url(offer['id'], jsonp_tag)
                yield scrapy.Request(offer_json_url,
                                     callback=self.parse_offer_details,
                                     headers=self.__class__._get_http_headers(meta['response.url']),
                                     meta=meta)


    def parse_offer_details(self, response):
        meta = response.meta
        # Parse Json
        return scrapy.Request(meta['deal']['landing_page'],
                              callback=self.parse_offer_stores,
                              headers=self.__class__._get_http_headers(meta['referer']),
                              meta=meta)

    def parse_offer_stores(self, response):
        # Parse store
        script = extract_first_value_with_xpath(
            '//section//div[@class="storemap-holder"]/following-sibling::script[1]/text()')

        idx = script.find('showOfferDetailNearStoreMap')
        if idx < 0:
            return None
        locations_json = substr_surrounded_by_chars(script, ('[', ']'), idx)
        store_locations = json_loads(locations_json)
        # [
        #     {id:14540226467431,latitude:-36.9424592,longitude:174.7867304,displayName:"FreshChoice -- Mangere Bridge'"}
        #     ,
        #     {id:14776308161975,latitude:-36.9446156,longitude:174.8425279,displayName:"FreshChoice -- Otahuhu'"}
        #     ,
        #     {id:14540226467325,latitude:-36.8809,longitude:174.8966,displayName:"FreshChoice -- Half Moon Bay'"}
        # ]
        pass
