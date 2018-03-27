# -*- coding: utf-8 -*-
__author__ = 'qinpeng'

import random
from datetime import datetime, timedelta
from json import loads as json_loads

import scrapy

from country.models import Country
from dealcrawler.spiders.BaseSpider import BaseSpider
from dealcrawler.util import *
from region.models import Region
from retailer.models import RetailerProperty
from source.models import DataSource
from store.models import Store, StoreProperty
from supersaver.constants import *
from supersaver.settings import make_internal_property_name
from ..data.retailer_repository import RetailerRepository
from .lasoo.util import *

UTC_TO_NZ_TIMEZONE_DELTA = timedelta(seconds=12*3600)


class LasooCoNzRetailerSpider(BaseSpider):

    """
    Crawl retailer and stores from lasoo.co.nz
    """
    name = 'retailer.lasoo.co.nz'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/48.0.2564.97 Safari/537.36',
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
    }

    ORIGIN_URL = 'https://www.lasoo.co.nz/retailers.html'
    INITIAL_REFERER_URL = 'https://www.lasoo.co.nz/retailers.html'

    REQUEST_HOST = 'www.lasoo.co.nz'

    # Filter parameter is single capital character 'ABCD...XYZ' or 0(zero)
    RETAILER_LIST_URL_FORMAT = 'https://www.lasoo.co.nz/retailers.html?filter={0}&requestType=ajax'
    NAME_INITIAL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0"

    # 1. Browser retailer list with initial character.
    #    Filter parameter is single capital character 'ABCD...XYZ' or 0(zero)
    # 2. Crawler retailer landing page.
    #    Retailer website link and logo may be found from retailer landing page:
    #    https://www.lasoo.co.nz/retailer/{retailer_name}.html
    # 3. Extract store lists link from retailer landing page, and get list of stores with pagination.
    #    https://www.lasoo.co.nz/storelocator.html?pid=findstores%28top%29
    #    You can get store lasoo id, name, geo location here.
    # 4. Get store location (Some retailer may not have store)
    #    https://www.lasoo.co.nz/storelocator/{retailer_name}/location/{region}.html
    # 5. Parse store name, id, address, open hours, phone number, fax

    def __init__(self, *args, **kwargs):
        start_urls = []
        for ch in self.__class__.NAME_INITIAL_CHARS:
            # Ajax requests on website to get retailer list
            start_urls.append(self.__class__.RETAILER_LIST_URL_FORMAT.format(ch))
        super().__init__(
            start_urls,
            self.__class__.REQUEST_HOST,
            *args, **kwargs)

        self.datasource = DataSource.objects.get(id=DATASOURCE_ID_LASOO_CO_NZ)
        self.country = Country.objects.get(country_code='NZ')

        self.retailer_repo = RetailerRepository(self.datasource, self.country)
        random.seed(datetime.now().timestamp())

        # TODO: Identify proper region for retailer stores
        self.region = Region.objects.get(name="all new zealand")

    def start_requests(self):
        for url in self.start_urls:
            yield self.create_request(url, self.parse, referer=self.__class__.INITIAL_REFERER_URL, dont_filter=True)

    def parse(self, response):
        for retailer_li in response.xpath('//div[@class="tab-pane"]/ul/li'):
            data = extract_first_value_with_xpath(retailer_li, "a/@data")
            retailer_id = json_loads(data)['objectid']
            display_name = extract_first_value_with_xpath(retailer_li, "a/@title")
            link = extract_first_value_with_xpath(retailer_li, "a/@href")
            retailer_detail_url = response.urljoin(link)

            retailer_data = {
                'id': retailer_id,
                'name': display_name,
                'lasoo_url': retailer_detail_url,
            }
            meta = {
                'retailer': retailer_data,
            }
            yield scrapy.Request(retailer_detail_url,
                                 callback=self.parse_retailer_details_from_response,
                                 headers=self.__class__._get_http_headers(self.__class__.INITIAL_REFERER_URL),
                                 meta=meta)

    def parse_retailer_details_from_response(self, response):
        elem = first_elem_with_xpath(response, '//div[@class="container"]//div[@class="banner"]//div[@class="content"]')
        data = response.meta["retailer"]
        logo_url = extract_first_value_with_xpath(elem, "img/@src")

        website = None
        store_list_url = None
        anchors = elem.xpath('a')
        for anchor_elem in anchors:
            text = extract_first_value_with_xpath(anchor_elem, 'span/text()')
            href = extract_first_value_with_xpath(anchor_elem, '@href')
            if text and "view website" == text.lower():
                if href:
                    if href.startswith('http'):
                        # External website
                        website = href
                    elif website != '#':
                        website = response.urljoin(href)
            elif href and href.startswith("/storelocator"):
                store_list_url = response.urljoin(href)
        props = []
        prop = RetailerProperty()
        prop.name = make_internal_property_name("lasoo_id")
        prop.value = data['id']
        props.append(prop)

        prop = RetailerProperty()
        prop.name = make_internal_property_name("lasoo_url")
        prop.value = data['lasoo_url']
        props.append(prop)
        retailer = self.retailer_repo.add_or_update_retailer_in_db(data['name'], website, logo_url, props)

        if store_list_url:
            meta = {
                "retailer": retailer
            }
            return scrapy.Request(store_list_url,
                                  callback=self.parse_stores_from_response,
                                  headers=self.__class__._get_http_headers(response.url),
                                  meta=meta)
        else:
            return None

    def parse_stores_from_response(self, response):
        retailer = response.meta["retailer"]
        script_elems = response.xpath("//section[contains(@class, 'store_listing')]/div/script/text()")
        stores_by_id = {}
        for elem in script_elems:
            script_text = elem.extract()
            idx = script_text.find("showOfferDetailNearStoreMap")
            if idx >= 0:
                store_json = substr_surrounded_by_chars(script_text, ('[', ']'), idx)
                stores = parse_lasoo_store_js(store_json)
                stores_by_id = {s['lasoo_id']: s for s in stores}
                break
        store_list_elems = response.xpath(
            "//section/div/div[contains(@class,'store-listing-table')]//tr[contains(@class,'ctr-storeitem')]")
        for elem in store_list_elems:
            # Get store url and address
            store_id = extract_first_value_with_xpath(elem, "@data-storeid")
            store = stores_by_id[store_id]
            store_url = extract_first_value_with_xpath(elem, "@data-url")
            address = extract_first_value_with_xpath(elem, "td[2]/text()")

            store['lasoo_url'] = response.urljoin(store_url)
            store['address'] = normalize_lasoo_store_address(address)
            meta = {
                "retailer": retailer,
                "store": store
            }
            yield scrapy.Request(response.urljoin(store_url),
                                 callback=self.parse_store_details_from_response,
                                 headers=self.__class__._get_http_headers(response.url),
                                 meta=meta)
        # Is there pagination button? If so, we can get more stores.
        next_page = extract_first_value_with_xpath(response, "//div[@class='pagination']//a[@class='next']/@href")
        if not next_page:
            return None
        meta = {
            "retailer": retailer
        }
        # Crawl stores in next page
        next_stores_page_url = response.urljoin(next_page)
        return scrapy.Request(next_stores_page_url,
                              callback=self.parse_stores_from_response,
                              headers=self.__class__._get_http_headers(response.url),
                              meta=meta)

    def parse_store_details_from_response(self, response):
        retailer = response.meta['retailer']
        store = response.meta['store']
        values = response.xpath(
            '//div[@class="storemap-holder"]/div[@class="storemap-info"]/div/strong/text()').extract()
        for v in values:
            if v.lower().startswith('ph:'):
                normalised_tel = v[3:].strip().replace(' ', '')
                store['tel'] = normalised_tel
                break
        working_hours_node = first_elem_with_xpath(response, '//section//div[@class="store_hour"]/div[@class="content"]')
        working_hours = self.__class__.extract_working_hours(working_hours_node)
        if working_hours:
            store['working_hours'] = working_hours
        # Save and update store and its properties in database
        add_or_update_store_in_db(store, self.region, retailer)
        return None

    @staticmethod
    def extract_working_hours(html_node):
        if exists_elem_with_xpath(html_node, '//table[@id="storeHours"]'):
            # A working hours table
            working_hours = ""
            is_header = True
            for row_node in html_node.xpath('//table[@id="storeHours"]//tr'):
                if is_header:
                    is_header = False
                    continue
                values = list(extract_values_with_xpath(row_node, 'td/text()'))
                if len(working_hours) > 0:
                    working_hours += "\n"
                working_hours += "{0} {1} - {2}".format(values[0], values[1], values[2])
            if len(working_hours) > 0:
                return working_hours
        else:
            working_hours = extract_first_value_with_xpath(html_node, 'text()')
            if working_hours.lower().find("no store hours") < 0:
                nv = working_hours.strip()
                return nv
        return None

    @classmethod
    def _get_http_headers(cls, referer):
        return {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.8',
            'Host': cls.REQUEST_HOST,
            'Referer': referer,
        }
