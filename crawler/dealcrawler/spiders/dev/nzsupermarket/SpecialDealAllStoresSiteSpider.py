import logging
from json import loads
from urllib import parse as urlparse
from datetime import datetime, timedelta
from dateutil import parser as dateparser

import scrapy

from retailer.models import Retailer
from category.models import Category
from store.models import Store
from region.models import Region

from dealcrawler.util import *
from dealcrawler.model.items import StoreItem, RegionItem


class SpecialDealAllStoresSiteSpider(scrapy.Spider):
    """
    Since FreshChoice and SuperValue have almost same site structure,
    this class is the super class for FreshChoice and SuperValue spiders.
    """
    name = "super-class-for-freshchoice-and-supervalue.com"
    settings = {
        "ROBOTSTXT_OBEY": False
    }

    def __init__(self, retailer_id, store_list_url, region_list_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retailer = Retailer.objects.get(id=retailer_id)
        self.region_list_url = region_list_url
        self.store_list_url = store_list_url
        self.regions_by_name = {}
        self.stores_by_name = {}
        self.category_by_css = {}
        self.debug_enabled = ('debug' in kwargs and kwargs['debug'].lower() == 'true')

    def start_requests(self):
        # Initial requests to start crawling
        # Create/Update regions and stores
        yield scrapy.http.Request(self.region_list_url, callback=self.create_or_update_regions)

    def parse(self, response):
        # Subclass should implement default response parse logic themselves.
        self.log(u'Please specify request callback for request {0}'.format(response.url))

    def debug_info(self, message):
        if self.debug_enabled:
            self.log(message)

    def create_or_update_regions(self, response):
        regions = Region.objects.filter(country__country_code='NZ')
        region_mapping = {r.name: r for r in regions}
        regions = []
        new_region_items = []
        selector = scrapy.Selector(response=response)
        for region_option in selector.xpath('//*[@id="catid"]/option'):
            region_id = region_option.extract_first_value_with_xpath('@value')
            if region_id == '-1':
                continue
            name = region_option.extract_first_value_with_xpath('./text()')
            item = RegionItem()
            item['name'] = name
            item['external_region_id'] = region_id
            item['active'] = True
            item['retailer'] = self.retailer
            new_region_items.append(item)
            if name in region_mapping:
                # Update original region
                region = region_mapping.pop(name)
                region.external_region_id = region_id
                region.active = True
                region.save()
            else:
                # Create new region.
                region = item.save()
            regions.append(region)

        # Make as inactive region to avoid breaking integrity of original data.
        for region in region_mapping.values():
            if region.active:
                region.active = False
                region.save()

        # Cache region for later store region field mapping
        self.regions_by_name = {r.name: r for r in regions}

        # Start update store list
        store_request = scrapy.http.Request(self.store_list_url,
                                            callback=self.create_or_update_stores)
        new_region_items.append(store_request)
        return new_region_items

    def create_or_update_stores(self, response):
        stores = Store.objects.filter(retailer=self.retailer)
        stores_by_name = {s.name: s for s in stores}
        stores = []
        selector = scrapy.Selector(response=response, type='xml')
        for store in selector.xpath('/markers/marker'):
            name = store.extract_first_value_with_xpath('./name/text()')
            region_name = store.extract_first_value_with_xpath('./category/text()')
            region = self.regions_by_name[region_name]
            address = store.extract_first_value_with_xpath('./address/text()')
            lat = store.extract_first_value_with_xpath('./lat/text()', func=float)
            lng = store.extract_first_value_with_xpath('./lng/text()', func=float)
            tel = store.extract_first_value_with_xpath('./phone/text()')
            working_hours = store.extract_first_value_with_xpath("./*[@name='Open']/text()")
            if region is None:
                self.log("Can't find region by name {0} for store {1}.".format(region_name, name))
            item = StoreItem()
            item['region'] = region
            item['name'] = name
            item['address'] = address
            item['latitude'] = lat
            item['longitude'] = lng
            item['tel'] = tel
            item['working_hours'] = working_hours
            item['provider_store_id'] = None
            item['active'] = True
            item['retailer'] = self.retailer
            if name in stores_by_name:
                # update original store
                store = stores_by_name.pop(name)
                store.name = name
                store.region = region
                store.latitude = lat
                store.longitude = lng
                store.address = address
                store.tel = tel
                store.working_hours = working_hours
                store.active = True
                store.save()
            else:
                # Create new store
                store = item.save()
            stores.append(store)
            yield item

        # Mark rest of stores as inactive
        for s in stores_by_name.values():
            if s.active:
                s.active = False
                s.save()
        self.stores_by_name = {s.name: s for s in stores}
        # After stores updated, we need to update products.
        self.debug_info(u'Start catalogue request: {0}'.format(self.__class__.catalogue_list_url))
        yield scrapy.http.Request(self.__class__.catalogue_list_url, callback=self.create_or_update_categories)

    def create_or_update_categories(self, response):
        json_result = loads(response.body.decode('utf8'))
        selector = scrapy.Selector(text=json_result['html'], type="html")
        categories = Category.objects.filter(active=True)
        category_by_name = {c.name.lower(): c for c in categories}
        category_by_css = {}
        for option in selector.xpath("//ul[contains(@class, 'dropdown-menu')]/li/a"):
            category_name = option.extract_first_value_with_xpath('./text()')
            if category_name == '':
                continue
            category_css_name = option.extract_first_value_with_xpath('./@value')
            lower_name = category_name.lower()
            if lower_name in category_by_name:
                cat = category_by_name.pop(lower_name)
                if not cat.active:
                    cat.name = category_name.capitalize()
                    cat.active = True
                    cat.save()
                    self.debug_info('Reactive category {0}'.format(category_name))
            else:
                cat = Category(name=category_name.capitalize(), active=True)
                cat.save()
                self.debug_info('Create new category {0}'.format(category_name))
            product_list_url = option.extract_first_value_with_xpath('./@href')
            url = urlparse.urljoin(self.__class__.catalogue_base_url, product_list_url)
            yield scrapy.http.Request(url, callback=self.create_or_update_products)
            category_by_css[category_css_name] = cat
        self.category_by_css = category_by_css

    def create_or_update_product(self, response):
        raise NotImplementedError

    @classmethod
    def _update_product(cls, prod, prod_item):
        """
        Update product data with latest data.
        """
        changed = False
        prod.description = prod_item['description']
        value = prod_item['price']
        if prod.price != value:
            prod.price = value
            changed = True
        value = prod_item['category']
        if prod.category_id != value.id:
            prod.category = value
            changed = True
        value = prod_item['unit']
        if prod.unit != value:
            prod.unit = value
            changed = True
        value = prod_item['remark']
        if prod.remark != value:
            prod.remark = value
            changed = True
        value = prod_item['promotion_start_date']
        if prod.promotion_start_date != value:
            prod.promotion_start_date = value
            changed = True
        value = prod_item['promotion_end_date']
        if prod.promotion_end_date != value:
            prod.promotion_end_date = value
            changed = True

        if changed:
            prod.save()
        return prod

    @classmethod
    def _parse_date_range(cls, week_date_range_str):
        """
        Parse date range string like '15th September - 21st September'.
        Return date range with UTC timezone.
        """
        # Parse date range as UTC time(The date range string is in NZ timezone).
        # Split with EN-DASH \u2013
        date_range = [(dateparser.parse(s.strip()) - UTC_TO_NZ_TIMEZONE_DELTA) for s in week_date_range_str.split(u'\u2013')]
        start_date, end_date = date_range[0], date_range[1]
        now = datetime.now()
        # Check if the date is in next year.
        # Should be the next year, if month of the date is less than current month.
        if start_date.month < now.month:
            start_date.replace(year=now.year + 1)
        if end_date.month < now.month:
            end_date.replace(year=now.year + 1)
        return start_date, end_date
