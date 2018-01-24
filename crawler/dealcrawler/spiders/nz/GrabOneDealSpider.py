# -*- coding: utf-8 -*-
import re
import sys
import logging
import traceback
from json import loads as json_loads
from urllib.parse import urlparse
from datetime import datetime
from dateutil.parser import parse as parse_date

from retailer.models import Retailer
from store.models import Store
from product.models import Product, ProductProperty, ProductImage
from supersaver.constants import *
from supersaver.settings import make_internal_property_name

from dealcrawler.spiders.BaseSpider import BaseSpider
from dealcrawler.util import *


class GrabOneDealSpider(BaseSpider):
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
            detail_url = data['prod'].landing_page
            yield self.create_request(
                detail_url,
                self.parse_deal_details_page,
                referer=response.url,
                meta=data)

    def parse_deal(self, response, elem, meta):
        retailer_name = extract_first_value_with_xpath(elem, './section/header/p[@class="listing-vendor"]/text()')
        retailer = self._get_retailer(retailer_name)
        if retailer is None:
            retailer = Retailer()
            retailer.name = retailer_name.lower()
            retailer.display_name = retailer_name
            retailer.datasource = self.datasource
            retailer.country = self.country
            retailer.save()
            self._add_or_update_retailer(retailer)

        url = extract_first_value_with_xpath(elem, './@href')
        landing_page = response.urljoin(url)
        prod = self._get_prod(landing_page)
        if prod is None:
            prod = Product()

        date_range = meta['meta']
        start_time, end_time = self.parse_date_range(date_range)

        prod.active = True
        prod.title = meta['title']
        prod.description = extract_first_value_with_xpath(elem, './a/span/img/@alt')
        prod.landing_page = response.urljoin(url)
        prod.promotion_start_date = start_time
        prod.promotion_end_date = end_time
        price_elem = first_elem_with_xpath(elem, './/div[@class="price-container"]')
        if price_elem is None:
            return None
        value = extract_first_value_with_xpath(price_elem, './span[@class="price"]/text()')
        prod.price = 0 if value is None else sanitize_price(value)
        value = extract_first_value_with_xpath(price_elem, './span[@class="value"]/text()')
        prod.saved = value
        #value = extract_first_value_with_xpath(price_elem, './span[@class="from"]/text()')
        #prod['from'] = value if value is None else value.strip()

        image_url = extract_first_value_with_xpath(elem, './a/span/img/@src')
        if image_url.find('placeholder') > 0:
            image_url = extract_first_value_with_xpath(elem, './a/span/img/@data-go-lazy-src')
        image_url_path = urlparse(image_url).path
        image_url = self.__class__.DEAL_IMAGE_URL_FORMAT.format(image_url_path[image_url_path.rindex('/')+1:])
        prod_image = ProductImage()
        prod_image.product = prod
        prod_image.original_url = image_url
        prod_image.unique_hash = str(datetime.now().timestamp())

        return {
            'prod': prod,
            'image': prod_image,
            'retailer': retailer
        }

    def parse_deal_details_page(self, response):
        region = response.meta['region']
        retailer = response.meta['retailer']
        self.retailer_by_name
        store = None
        prod = response.meta['prod']
        prod_image = response.meta['image']
        prod_property = None
        prod.retailer = retailer

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
            prod_property = ProductProperty()
            prod_property.product = prod
            prod_property.name = make_internal_property_name('grabone_product_id')
            prod_property.value = data['productID']

        for script_text in extract_values_with_xpath(elem_root, './script[not(@type)]/text()'):
            if script_text.find('.viewProduct') < 0:
                continue
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
            location = merchant_locations[0]

            store_name = retailer.display_name
            store_title = str.strip(location['title'])
            lat, lng = location['lat'], location['lng']
            address = str.strip(location['physical_address_plain_text'])
            address = address.replace('\u00a0', ', ') if address is not None else None
            if len(address) > 512:
                self.log('Product {0}: Store address is too long ({1}).'.format(prod.landing_page, address))
                address = address[:512]
            website, tel = None, None
            for contact_elem in response.xpath('//div[@class="supplier-info"]/a'):
                if len(contact_elem.xpath('./i[contains(@class, "fa-globe")]')) > 0:
                    website = extract_first_value_with_xpath(contact_elem, './@href')
                elif len(contact_elem.xpath('./i[contains(@class, "fa-phone")]')) > 0:
                    tel = extract_first_value_with_xpath(contact_elem, './@tel')
            try:
                store = retailer.stores.get(name=store_name, latitude=lat, longitude=lng)
            except Store.DoesNotExist:
                store = Store()
            store.region = region
            store.retailer = retailer
            store.name = store_name
            store.latitude = lat
            store.longitude = lng
            store.address = address
            store.website = website
            store.tel = tel
            store.save()

        # Save product data to database
        prod.retailer = retailer
        prod.store = store
        prod.save()
        self._add_or_update_prod(prod)
        if prod_image is not None and prod_image.pk is None:
            try:
                # TODO: Hash
                existing_image = prod.product_images.get(original_url=prod_image.original_url)
                prod_image = existing_image
            except ProductImage.DoesNotExist:
                # Image not saved
                prod_image.product = prod
                prod_image.save()
        if prod_property is not None:
            prod_property.save()
        return {}

    def parse_date_range(self, date_range_str):
        tz_delta = datetime.now() - datetime.utcnow()
        # parse date time as UTC time
        date_pair_str = date_range_str.split('|')[0]
        try:
            dates = list(map(lambda s: parse_date(s.strip()) - tz_delta, date_pair_str.split('-')))
            return int(dates[0].timestamp()), int(dates[1].timestamp())
        except:
            self.log('Invalid date range {0}.\nError: {1}'.format(data_range_str, sys.exc_info()), level=logging.ERROR)
            raise
