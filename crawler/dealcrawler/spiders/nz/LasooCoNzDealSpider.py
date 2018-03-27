__author__ = 'qinpeng'

import logging
import random
from datetime import datetime, timedelta

import scrapy
from dateutil import parser as dateparser

from dealcrawler.model.items import ProductItem
from dealcrawler.spiders.BaseSpider import DealSpider
from dealcrawler.util import *
from product.models import ProductProperty
from region.models import Region
from retailer.models import RetailerProperty
from supersaver.constants import *
from .lasoo.util import *

UTC_TO_NZ_TIMEZONE_DELTA = timedelta(seconds=12*3600)


class LasooCoNzDealSpider(DealSpider):

    """
    Crawl deals from lasoo.co.nz
    Notes:
    Make sure LasooCoNzRetailerSpider has been ran before this crawler to get updated retailer and stores.
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
        # TODO: Identify proper region for retailer stores
        self.region = Region.objects.get(name="all new zealand")

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
        catalogue_url = self.__class__._get_deals_url(response.meta['catalogue_id'], jsonp_tag)
        meta = response.meta
        meta['offer_start_date'] = start_date
        meta['offer_end_date'] = end_date
        meta['retailer'] = retailer
        meta['jsonp_tag'] = jsonp_tag
        yield scrapy.Request(catalogue_url,
                             callback=self.parse_catalogue_from_response,
                             headers=self.__class__._get_http_headers(meta['referer']),
                             meta=meta)

    def _get_retailer_from_json(self, retailer_json):
        retailer_name = retailer_json['name']
        retailer = self.retailer_repo.get_retailer_by_name(retailer_name)
        # Retailer normally should be already in DB, if not we create a new one.
        if retailer:
            return retailer
        properties = []
        prop = RetailerProperty()
        prop.name = make_internal_property_name('lasoo_id')
        prop.value = str(retailer_json['id'])
        properties.append(prop)

        prop = RetailerProperty()
        prop.name = make_internal_property_name('lasoo_unique_name')
        prop.value = str(retailer_json['uniqueName'])
        properties.append(prop)

        prop = RetailerProperty()
        prop.name = make_internal_property_name('lasoo_code')
        prop.value = str(retailer_json['code'])
        properties.append(prop)

        return self._create_or_update_retailer_in_db(retailer_name, None, retailer_json['smallImage'], properties)

    def parse_catalogue_from_response(self, response):
        retailer = response.meta['retailer']
        offer_start_time = response.meta['offer_start_date']
        offer_end_time = response.meta['offer_end_date']

        deals_data = self._get_jsonp_response_data(response.body, response.meta['jsonp_tag'])
        # TODO: Extract categories
        # if 'categoryPath' in offer:
        #     cats = offer['categoryPath']
        #     for c in cats:
        #         category = SourceCategory()
        #         c.name = c['uniqueName']
        #         c.source_category_id = c['id']
        #         c.display_name = c['name']
        #         c.source = self.datasource
        #         c.save()

        referer = response.meta['referer']
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

                lasoo_url = response.urljoin(offer_data['landingLink'])
                if 'url' in offer_data and offer_data['url']:
                    offer['landing_page'] = offer_data['url']
                else:
                    offer['landing_page'] = lasoo_url
                meta = {
                    'offer': offer,
                    'lasoo_url': lasoo_url,
                    'referer': referer,
                    'retailer': retailer,
                }
                if 'offerimage' in offer_data:
                    meta['offer_image'] = offer_data['offerimage']['path']
                # Update jsonp for new request
                jsonp_tag = self.__class__._get_random_jsonp_tag()
                meta['jsonp_tag'] = jsonp_tag
                offer_json_url = self.__class__._get_offer_url(offer_data['id'], jsonp_tag)
                yield scrapy.Request(offer_json_url,
                                     callback=self.parse_offer_details_from_response,
                                     headers=self.__class__._get_http_headers(referer),
                                     meta=meta)

    def parse_offer_details_from_response(self, response):
        # Parse Json
        data = self._get_jsonp_response_data(response.body, response.meta['jsonp_tag'])
        if len(data) == 0:
            self.log('Failed to get offer details {0}'.format(response.url), level=logging.WARN)
            return
        retailer = response.meta['retailer']
        offer_data = data[0]
        offer = response.meta['offer']
        offer['price'] = offer_data['priceValue']
        offer['saved'] = \
            None if 'saving' not in offer_data or not offer_data['saving'] else offer_data['saving']
        description = \
            "" if 'description' not in offer_data or not offer_data['description'] else offer_data['description']
        # Limit to max length in Product.description column
        offer['description'] = description[:512]

        props = []
        prop = ProductProperty()
        prop.name = make_internal_property_name('lasoo_id')
        prop.value = offer_data['id']
        props.append(prop)

        offer_image = None if 'offer_image' not in response.meta else response.meta['offer_image']
        lasoo_url = None if 'lasoo_url' not in response.meta else response.meta['lasoo_url']
        if lasoo_url:
            prop = ProductProperty()
            prop.name = make_internal_property_name('lasoo_url')
            prop.value = lasoo_url
            props.append(prop)
        db_offer = self.prod_repo.add_or_update_prod_in_db(offer, offer_image, stores=None, properties=props)
        if lasoo_url:
            meta = {
                'db_offer': db_offer,
                'retailer': retailer,
            }
            # Parse stores for this deal.
            return scrapy.Request(lasoo_url,
                                  callback=self.parse_offer_stores_response,
                                  headers=self.__class__._get_http_headers(response.meta['referer']),
                                  meta=meta)
        else:
            return offer

    def parse_offer_stores_response(self, response):
        # Parse store
        script = extract_first_value_with_xpath(
            response, '//section//div[@class="storemap-holder"]/following-sibling::script[1]/text()')

        idx = script.find('showOfferDetailNearStoreMap')
        if idx < 0:
            return None
        locations_json = substr_surrounded_by_chars(script, ('[', ']'), idx)
        store_locations = parse_lasoo_store_js(locations_json)

        offer = response.meta['db_offer']
        retailer = response.meta['retailer']
        for store in store_locations:
            stores = Store.objects.filter(
                retailer=retailer,
                properties__name=make_internal_property_name('lasoo_id'),
                properties__value=store['lasoo_id'])
            if len(stores) > 0:
                offer.stores.add(stores[0])
            else:
                db_store = add_or_update_store_in_db(store, self.region, retailer)
                offer.stores.add(db_store)


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
