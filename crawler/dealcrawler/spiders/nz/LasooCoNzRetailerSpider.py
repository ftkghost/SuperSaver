__author__ = 'qinpeng'

import logging
from json import loads as json_loads
from urllib import parse as urlparse
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import random

import scrapy
from supersaver.settings import make_internal_property_name

from dealcrawler.spiders.BaseSpider import BaseSpider
from retailer.models import Retailer, RetailerProperty
from category.models import Category
from store.models import Store
from region.models import Region
from product.models import Product, ProductImage
from supersaver.constants import *
from product.models import ProductProperty

from dealcrawler.util import *
from dealcrawler.model.items import ProductItem, StoreItem, RegionItem


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

    REQUEST_HOST = 'www.lasoo.co.nz'

    # Filter parameter is single capital character 'ABCD...XYZ' or 0(zero)
    RETAILER_LIST_URL_FORMAT = 'https://www.lasoo.co.nz/retailers.html?filter={0}&requestType=ajax'
    NAME_INITIAL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0"

    # 1. Filter parameter is single capital character 'ABCD...XYZ' or 0(zero)
    # 2. Retailer website link and logo may be found from retailer landing page:
    #    https://www.lasoo.co.nz/retailer/{retailer_name}.html
    # 3 Store lists
    #    https://www.lasoo.co.nz/storelocator.html?pid=findstores%28top%29
    # 4. Get store location (Some retailer may not have store)
    #    https://www.lasoo.co.nz/storelocator/{retailer_name}/location/{region}.html
    # 5. Parse store name, id, address, open hours
    # //div[class='storemap-info']/div/h2/
    # <h2 class="element_left onload_tracking" data="{&quot;placement&quot;:&quot;Store Details&quot;,&quot;object&quot;:&quot;store&quot;,&quot;objectid&quot;:&quot;14565330054621&quot;,&quot;interaction&quot;:&quot;&quot;}">The Warehouse -- South City</h2>
    #
    # Opening hours:
    # //div[class="store_hour"]/div/table/tbody/tr
    #
    # Other stores:
    # //div[class="additional_stores"]/div/table/tbody/tr
    #
    # https://www.jbhifi.co.nz/Stores/Store-Finder/
    # //ul[id='stores']/li/div//ul/li
    # <li ng-repeat="Store in State.Stores" id="14" data-lat="-36.728873" data-long="174.711721" data-phone="09 968 6967" data-adr="219 Don McKinnon Drive, Albany, 0632 NORTH ISLAND" data-today="9:00a.m. - 6:00p.m." data-tomorrow="9:00a.m. - 6:00p.m." class="ng-scope">
    #   <a data-bind="storeLink: $data, text: StoreName" href="/Stores/../Stores/Store-Finder/Store-List/north-island/albany/" title="Albany" class="ng-binding">Albany</a>
    # </li>

    def __init__(self, *args, **kwargs):
        start_urls = []
        for ch in self.__class__.NAME_INITIAL_CHARS:
            # Ajax requests on website to get retailer list
            start_urls.append(self.__class__.RETAILER_LIST_URL_FORMAT.format(ch))
        super().__init__(
            DATASOURCE_ID_LASOO_CO_NZ,
            'NZ',
            start_urls,
            self.__class__.REQUEST_HOST,
            *args, **kwargs)
        random.seed(datetime.now().timestamp())

    # TODO: Parse retailer list and store list first with higher request priority
    def parse(self, response):
        for retailer_li in response.xpath('//div[@class="tab-pane"]/ul/li'):
            data = extract_first_value_with_xpath(retailer_li, "a/@data")
            retailer_id = json_loads(data)['objectid']
            display_name = extract_first_value_with_xpath(retailer_li, "a/@title")
            link = extract_first_value_with_xpath(retailer_li, "a/@href")
            retailer_detail_url = response.urljoin(link)

            retailer_data = {
                'id': retailer_id,
                'display_name': display_name,
                'lasoo_url': retailer_detail_url,
            }
            meta = {
                'retailer': retailer_data,
            }
            yield scrapy.Request(retailer_detail_url,
                                 callback=self.parse_retailer_details_from_response,
                                 headers=self.__class__._get_http_headers(response.url),
                                 meta=meta)

    def parse_retailer_details_from_response(self, response):
        elem = first_elem_with_xpath(response, '//div[@class="container"]//div[@class="banner"]//div[@class="content"]')
        retailer = response.meta["retailer"]
        retailer['logo_url'] = extract_first_value_with_xpath(elem, "img/@src")
        website_text = extract_first_value_with_xpath(elem, 'a/span/text()')
        if "View Website" == website_text:
            website = extract_first_value_with_xpath(elem, 'a[contains(@class, "lzbtn")]/@href')
            if not website:
                if website.startswith('http'):
                    # External website
                    retailer['website'] = website
                elif website != '#':
                    retailer['website'] = response.urljoin(website)
        return retailer

    @classmethod
    def _get_http_headers(cls, referer):
        return {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.8',
            'Host': cls.REQUEST_HOST,
            'Referer': referer,
        }