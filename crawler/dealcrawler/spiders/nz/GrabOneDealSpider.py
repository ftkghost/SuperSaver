# -*- coding: utf-8 -*-
import logging
import re
import sys
import traceback
from datetime import datetime, timedelta
from json import loads as json_loads

from dateutil.parser import parse as parse_date

from dealcrawler.model.items import ProductItem
from dealcrawler.spiders.BaseSpider import DealSpider
from dealcrawler.util import *
from product.models import ProductProperty
from store.models import Store
from supersaver.constants import *
from supersaver.settings import make_internal_property_name


class GrabOneDealSpider(DealSpider):
    name = 'grabone.co.nz'

    custom_settings = {
        'DEBUG': True,
        'DOWNLOAD_DELAY': 3
    }

    DEAL_IMAGE_URL_FORMAT = 'https://main-cdn.grabone.co.nz/goimage/fullsize/{0}'

    def __init__(self, *args, **kwargs):
        super().__init__(
            DATASOURCE_ID_GRABONE_CO_NZ,
            'NZ',
            'https://new.grabone.co.nz/auckland/search?limit=100&sortby=new',
            'new.grabone.co.nz',
            *args, **kwargs)
        self.category_by_name = {}
        self.logging_level = logging.DEBUG

    def parse(self, response):
        region_mapping = {name: {'region': self.region_by_name[name]} for name in self.region_by_name}
        for region_elem in response.xpath('//ul[@id="region-dropdown"]/li'):
            # The active region name may get 2 selectors if use 'text()' in xpath.
            region_name = ''.join(region_elem.xpath('./a/text()').extract()).strip()
            region_url = extract_first_value_with_xpath(region_elem, './a/@href')
            region_url = response.urljoin(region_url)
            data = region_mapping[region_name.lower()]
            data['region_url'] = region_url

        for cat_elem in response.xpath('//div[@id="search-filter-categories-menu"]/ul/li/div/label/a'):
            category_name = extract_first_value_with_xpath(cat_elem, './text()')
            if category_name.lower() == 'all categories':
                continue
            category_url = extract_first_value_with_xpath(cat_elem, './@href')
            category_url = response.urljoin(category_url)
            self.category_by_name[category_name] = {
                'category_name': category_name,
                'category_url': category_url
            }

        self.log('Regions: %d' % len(self.region_by_name))
        self.log('Categories: %d' % len(self.category_by_name))
        region_data = region_mapping['auckland']
        response.meta.update(**region_data)
        for request in self.parse_paginated_deals_page(response):
            yield request

        for name in region_mapping:
            region_data = region_mapping[name]
            if 'region_url' not in region_data:
                continue
            url = region_data['region_url']
            yield self.create_request(
                url,
                self.parse_paginated_deals_page,
                referer=response.url,
                meta=region_data)

    def parse_paginated_deals_page(self, response):
        pages = 0
        for page_url in extract_values_with_xpath(response, '//ul[@class="pagination"]/li/a/@href'):
            value = 0
            if page_url is not None:
                m = re.search('page=(?P<pages>[0-9]+)', page_url)
                if m:
                    value = int(m.group('pages'))
            if value > pages:
                pages = value
        self.log('#Total pages: {0} in {1}'.format(pages, response.url))
        # Crawl paginated deals
        for i in range(1, pages+1):
            query = '?sortby=new&page={0}'.format(i)
            url = response.urljoin(query)
            yield self.create_request(
                   url,
                   self.parse_deals_page,
                   meta=response.meta)
        # Crawl deals in this web page.
        for request in self.parse_deals_page(response):
            yield request

    def parse_deals_page(self, response):
        index = 0
        for deal_elem in response.xpath('//div[@id="search-grid-listings"]/article/div/a'):
            index += 1
            try:
                data = self.parse_deal(response, deal_elem)
            except:
                data = None
                self.log("Failed to parse deal {0} in {1}\n"
                         "Error: {2}".format(index, response.url, traceback.format_exc()))
            if data is None:
                continue
            data['region'] = response.meta['region']
            # Get deal details, store location and categories
            detail_url = data['prod']['landing_page']
            yield self.create_request(
                detail_url,
                self.parse_deal_details_page,
                referer=response.url,
                meta=data)

    def parse_deal(self, response, elem):
        retailer_name = extract_first_value_with_xpath(elem, './section/header/p[@class="listing-vendor"]/text()')
        retailer = self._create_or_update_retailer_in_db(retailer_name)

        prod = ProductItem()
        prod['retailer'] = retailer
        url = extract_first_value_with_xpath(elem, './@href')
        prod['landing_page'] = response.urljoin(url)
        value = elem.xpath('./section/header/h3[1]/text()').extract()
        if value:
            value = ''.join(value).strip(' \t\n\r')
            prod['title'] = value
        # prod['description'] = extract_first_value_with_xpath(elem, './figure/figcaption/p/text()')
        prod['description'] = extract_first_value_with_xpath(
            elem, './figure/img/@alt', default='')

        price_elem = first_elem_with_xpath(elem, './/div[@class="listing-price-container"]')
        if price_elem is None:
            return None
        prod['unit'] = ''
        value = extract_first_value_with_xpath(price_elem, './div[@class="listing-price-current"]/span/text()')
        original_price = 0 if (value is None or value == 'View offer') else sanitize_price(value)

        value = price_elem.xpath('.//div[@class="listing-price-current"]/text()').extract()
        if value:
            value = ''.join(value).strip(' \t\n\r')
        price = 0 if (value is None or len(value) == 0) else sanitize_price(value)
        if price == 0:
            value = extract_first_value_with_xpath(price_elem, './/div[@class="listing-price-per-item"]/text()')
            price = 0 if (value is None or len(value) == 0) else sanitize_price(value)
            if price > 0:
                prod['price'] = price
                prod['unit'] = 'each'
            else:
                prod['price'] = 0
        else:
            prod['price'] = price

        if original_price > 0 and original_price > price:
            prod['saved'] = 'from ${0}'.format(original_price)
        prod['active'] = True

        image_url = extract_first_value_with_xpath(elem, './figure/img/@data-go-lazy-src')
        if image_url and not image_url.startswith('http'):
            image_url = response.urljoin(image_url)

        return {
            'prod': prod,
            'image': image_url
        }

    def parse_deal_details_page(self, response):
        stores = []
        prod = response.meta['prod']
        prod_image = response.meta['image']
        prod_property = None

        elem_root = first_elem_with_xpath(response, '//div[@class="background-image-takeover"]')
        for script in extract_values_with_xpath(elem_root, './script[@type="application/ld+json"]/text()'):
            try:
                data = json_loads(script)
            except:
                self.log('Invalid category json in {0}'.format(response.url), level=logging.WARN)
                continue
            if 'category' not in data:
                continue
            # TODO: Parse category   data['category']

            start_time, end_time = None, None
            if 'offers' in data:
                offers = data['offers']
                if 'validFrom' in offers:
                    value = offers['validFrom']
                    start_time = int(parse_date(value).timestamp())
                if 'validThrough' in offers:
                    value = offers['validThrough']
                    end_time = int(parse_date(value).timestamp())
            if not start_time:
                start_time = int(datetime.now().timestamp())
            if not end_time:
                value = datetime.now() + timedelta(hours=24*7)
                end_time = int(value.timestamp())

            prod['promotion_start_date'] = start_time
            prod['promotion_end_date'] = end_time

            prod_property = ProductProperty()
            prod_property.name = make_internal_property_name('grabone_id')
            prod_property.value = data['productID']

        for script_text in extract_values_with_xpath(elem_root, './script[not(@type)]/text()'):
            if script_text.find('.viewProduct') < 0:
                continue
            idx = script_text.find('variants')
            if idx > 0:
                data = substr_surrounded_by_chars(script_text, ('[', ']'), idx)
                variants = json_loads(data)
                if len(variants) > 0 and 'buy_link' in variants[0] and len(variants[0]['buy_link']) > 0:
                    prod['fast_buy_link'] = variants[0]['buy_link']

            idx = script_text.find('merchantLocations')
            if idx < 0:
                self.log("Can't find merchantLocations in script, "
                         "please check the web content {0}.".format(response.url),
                         level=logging.WARNING)
                continue
            data = substr_surrounded_by_chars(script_text, ('[', ']'), idx)
            merchant_locations = json_loads(data)
            if merchant_locations is None or len(merchant_locations) < 1:
                continue
            for location in merchant_locations:
                store = self.parse_store_from_location(response, prod['retailer'], location)
                stores.append(store)

        props = list() if prod_property is None else [prod_property]
        self._create_or_update_prod_in_db(prod, prod_image, stores, props)
        return None

    def parse_store_from_location(self, response, retailer, location):
        store_name = retailer.display_name
        lat, lng, address = None, None, None    # no physical store, website only
        if ('lat' in location and len(location['lat']) > 0) \
                and ('lng' in location and len(location['lng']) > 0):
            lat = float(location['lat'])
            lng = float(location['lng'])
        if 'physical_address_plain_text' in location:
            address_value = str.strip(location['physical_address_plain_text'])
            if len(address_value) > 0:
                address_value = address_value.replace('\u00a0', ', ') if address_value is not None else None
                if len(address_value) > 512:
                    self.log('Product {0}: Store address is too long ({1}).'.format(response.url, address))
                address = address_value[:512]
        website, tel = None, None
        for contact_elem in response.xpath('//div[@class="supplier-info"]/a'):
            if len(contact_elem.xpath('./i[contains(@class, "fa-globe")]')) > 0:
                website = extract_first_value_with_xpath(contact_elem, './@href')
            elif len(contact_elem.xpath('./i[contains(@class, "fa-phone")]')) > 0:
                tel = extract_first_value_with_xpath(contact_elem, './text()')
        try:
            store = retailer.stores.get(name=store_name, latitude=lat, longitude=lng)
        except Store.DoesNotExist:
            store = Store()
        store.region = response.meta['region']
        store.retailer = retailer
        store.name = store_name
        store.latitude = lat
        store.longitude = lng
        store.address = address
        store.website = website
        store.tel = tel
        store.working_time = location['public_opening_hours']
        store.save()
        return store

    def parse_date_range(self, date_range_str):
        tz_delta = datetime.now() - datetime.utcnow()
        # parse date time as UTC time
        date_pair_str = date_range_str.split('|')[0]
        try:
            dates = list(map(lambda s: parse_date(s.strip()) - tz_delta, date_pair_str.split('-')))
            return int(dates[0].timestamp()), int(dates[1].timestamp())
        except:
            self.log('Invalid date range {0}.\nError: {1}'.format(date_range_str, sys.exc_info()), level=logging.ERROR)
            raise
