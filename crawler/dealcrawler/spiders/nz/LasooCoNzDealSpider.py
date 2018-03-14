__author__ = 'qinpeng'

import logging
import random
from datetime import datetime, timedelta
from json import loads as json_loads

import scrapy
from dateutil import parser as dateparser

from dealcrawler.model.items import ProductItem
from dealcrawler.spiders.BaseSpider import DealSpider
from dealcrawler.util import *
from product.models import ProductProperty
from retailer.models import RetailerProperty
from store.models import Store
from supersaver.constants import *
from supersaver.settings import make_internal_property_name

UTC_TO_NZ_TIMEZONE_DELTA = timedelta(seconds=12*3600)


class LasooCoNzDealSpider(DealSpider):

    """
    Crawl deals from lasoo.co.nz
    """
    name = 'lasoo.co.nz'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/48.0.2564.97 Safari/537.36',
    custom_settings = {
        'ROBOTSTXT_OBEY': False,

    }

    # SVER = 'ikt3z7fsszp9rt201651'
    ORIGIN_URL = 'https://www.lasoo.co.nz/'

    REQUEST_HOST = 'www.lasoo.co.nz'
    CATALOGUE_INFO_URL_FORMAT = 'https://www.lasoo.co.nz/data.js?type=catalogue' \
                               '&catalogueids={0}&jsonp={1}'
    RETAILER_DEALS_URL_FORMAT = 'https://www.lasoo.co.nz/data.js?type=cataloguepage' \
                                '&catalogueid={0}&allpages=1&jsonp={1}'
    OFFER_DETAILS_URL_FORMAT = 'https://www.lasoo.co.nz/data.js?type=offer&id={0}&jsonp={1}'

    def __init__(self, *args, **kwargs):
        super().__init__(
            DATASOURCE_ID_LASOO_CO_NZ,
            'NZ',
            self.__class__.ORIGIN_URL,
            self.__class__.REQUEST_HOST,
            *args, **kwargs)
        random.seed(datetime.now().timestamp())

    # TODO: Parse retailer list and store list first with higher request priority

    def parse(self, response):
        for cat_elem in response.xpath('//ul[contains(@class, "catalogue-list")]/li/div/a'):
            cat_detail_url = response.urljoin(extract_first_value_with_xpath(cat_elem, '@href'))
            cat_json_data = extract_first_value_with_xpath(cat_elem, '@data')
            data = json_loads(cat_json_data)
            if data['object'] == 'catalogue':
                catalogue_id = data['objectid']
                jsonp_tag = self.__class__._get_random_jsonp_tag()
                retailer_detail_url = self.__class__._get_retailer_detail_url(catalogue_id, jsonp_tag)
                yield scrapy.Request(retailer_detail_url,
                                     callback=self.parse_retailer_from_response,
                                     headers=self.__class__._get_http_headers(cat_detail_url),
                                     meta={
                                         'catalogue_id': catalogue_id,
                                         'referer': cat_detail_url,
                                         'jsonp_tag': jsonp_tag,
                                     })
                break  # To remove
            else:
                self.log("unknown catalogue object ({0}). {1}", cat_detail_url, data)

    def parse_retailer_from_response(self, response):
        json_data = self.__class__._get_jsonp_response_data(response.body, response.meta['jsonp_tag'])
        catalogues = json_data['catalogues']
        if len(catalogues) == 0:
            return []
        catalogue = catalogues[0]
        start_date = dateparser.parse(catalogue['startDate']).timestamp()
        end_date = dateparser.parse(catalogue['expiryDate']).timestamp()
        total_pages = catalogue['numberPages']
        retailer_data = catalogue['retailer']
        retailer = self._get_retailer_from_json(retailer_data)

        # Update jsonp for new request
        jsonp_tag = self.__class__._get_random_jsonp_tag()
        deal_url = self.__class__._get_deals_url(response.meta['catalogue_id'], jsonp_tag)
        meta = response.meta
        meta['offer_start_date'] = start_date
        meta['offer_end_date'] = end_date
        meta['retailer'] = retailer
        meta['jsonp_tag'] = jsonp_tag
        yield scrapy.Request(deal_url,
                             callback=self.parse_deals_from_response,
                             headers=self.__class__._get_http_headers(meta['referer']),
                             meta=meta)

    def _get_retailer_from_json(self, retailer_json):
        properties = []
        prop = RetailerProperty()
        prop.name = make_internal_property_name('lasoo_id')
        prop.value = retailer_json['id']
        properties.append(prop)

        prop = RetailerProperty()
        prop.name = make_internal_property_name('lasoo_unique_name')
        prop.value = retailer_json['uniqueName']
        properties.append(prop)

        prop = RetailerProperty()
        prop.name = make_internal_property_name('lasoo_code')
        prop.value = retailer_json['code']
        properties.append(prop)

        return self._create_or_update_retailer_in_db(retailer_json['name'], retailer_json['smallImage'], properties)

    def parse_deals_from_response(self, response):
        retailer = response.meta['retailer']
        offer_start_time = response.meta['offer_start_date']
        offer_end_time = response.meta['offer_end_date']

        deals_data = self._get_jsonp_response_data(response.body, response.meta['jsonp_tag'])
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
            for offer_data in offers:
                if offer_data['type'] != 'offer':
                    continue
                offer = ProductItem()
                offer['retailer'] = retailer
                offer['title'] = offer_data['title']
                offer['promotion_start_date'] = offer_start_time
                offer['promotion_end_date'] = offer_end_time
                offer['landing_page'] = response.urljoin(offer_data['landingLink'])

                meta = {
                    'offer': offer,
                    'referer': response.url,
                }
                if 'offerimage' in offer_data:
                    meta['offer_image'] = offer_data['offerimage']['path']
                # Update jsonp for new request
                jsonp_tag = self.__class__._get_random_jsonp_tag()
                meta['jsonp_tag'] = jsonp_tag
                offer_json_url = self.__class__._get_offer_url(offer_data['id'], jsonp_tag)
                yield scrapy.Request(offer_json_url,
                                     callback=self.parse_offer_details_from_response,
                                     headers=self.__class__._get_http_headers(response.url),
                                     meta=meta)

    def parse_offer_details_from_response(self, response):
        # Parse Json
        data = self._get_jsonp_response_data(response.body, response.meta['jsonp_tag'])
        if len(data) == 0:
            self.log('Failed to get offer details {0}'.format(response.url), level=logging.WARN)
            return
        offer_data = data[0]
        offer = response.meta['offer']
        offer['price'] = offer_data['priceValue']
        offer['saved'] = None if offer_data['saving'] is None or len(offer_data['saving']) else offer_data['saving']

        prop = ProductProperty()
        prop.name = make_internal_property_name('lasoo_id')
        prop.value = offer_data['id']

        meta = {
            'offer': offer,
            'offer_property': prop,
        }
        if 'offer_image' in response.meta:
            meta['offer_image'] = response.meta['offer_image']
        return scrapy.Request(offer['landing_page'],
                              callback=self.parse_offer_stores_response,
                              headers=self.__class__._get_http_headers(meta['referer']),
                              meta=meta)

    def parse_offer_stores_response(self, response):
        # Parse store
        script = extract_first_value_with_xpath(
            '//section//div[@class="storemap-holder"]/following-sibling::script[1]/text()')

        idx = script.find('showOfferDetailNearStoreMap')
        if idx < 0:
            return None
        locations_json = substr_surrounded_by_chars(script, ('[', ']'), idx)
        store_locations = json_loads(locations_json)
        offer = response.meta['offer']
        for l in store_locations:
            s = Store()
            s.retailer = offer.retailer
            name = l['displayName'].replace(' -- ', ' - ')
            s.name = name
            s.display_name = name
            s.latitude = l['latitude']
            s.longitude = l['longitude']

        # [
        #     {id:14540226467431,latitude:-36.9424592,longitude:174.7867304,displayName:"FreshChoice -- Mangere Bridge'"}
        #     ,
        #     {id:14776308161975,latitude:-36.9446156,longitude:174.8425279,displayName:"FreshChoice -- Otahuhu'"}
        #     ,
        #     {id:14540226467325,latitude:-36.8809,longitude:174.8966,displayName:"FreshChoice -- Half Moon Bay'"}
        # ]

    @classmethod
    def _get_random_jsonp_tag(cls):
        return 'mf%d' % random.randrange(100000000, 999999999)

    @classmethod
    def _get_retailer_detail_url(cls, catalogue_id, jsonp_tag):
        return cls.CATALOGUE_INFO_URL_FORMAT.format(catalogue_id, jsonp_tag)

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
            'Host': cls.REQUEST_HOST,
            'Referer': referer,
        }
