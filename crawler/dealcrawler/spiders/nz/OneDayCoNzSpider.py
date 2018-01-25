# -*- coding: utf-8 -*-
import re
import traceback
from datetime import datetime, timedelta

from supersaver.constants import RETAILER_NAME_1_DAY_CO_NZ
from retailer.models import Retailer
from product.models import Product
from supersaver.constants import DATASOURCE_ID_1_DAY_CO_NZ

from dealcrawler.model.items import ProductItem
from dealcrawler.spiders.BaseSpider import BaseSpider
from dealcrawler.util import *


class OneDayCoNzSpider(BaseSpider):
    """
    Crawl deals from 1-day.co.nz
    Scrapy reports error when trying to download subsequence pages with https, should update scrapy.http.cookies
    Ref: http://stackoverflow.com/questions/16559929/scrap-website-using-scrapy
    """
    name = '1-day.co.nz'

    custom_settings = {
        'DEBUG': True,
    }

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) ' \
                 'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/48.0.2564.97 Safari/537.36'

    def __init__(self, *args, **kwargs):
        # TODO: http://1-day.winecentral.co.nz/collections/all
        super().__init__(
            DATASOURCE_ID_1_DAY_CO_NZ,
            'NZ',
            'https://www.1-day.co.nz/',
            'www.1-day.co.nz',
            *args, **kwargs)
        self.retailer = Retailer.objects.get(name=RETAILER_NAME_1_DAY_CO_NZ)
        self.store = self.retailer.stores.filter(active=True).order_by('id')[0]

    def parse(self, response):
        # Top Ad Deals
        deals = extract_values_with_xpath(
            response, '//div[contains(@class, "main_holder")]//div[contains(@class, "top-image")]//a/@href')
        for relative_url in deals:
            url = response.urljoin(relative_url)
            self.log("Deal url: %s" % url)
            yield self.create_request(url, self.parse_today_deals_list)

        # Home Page Deals
        deals = extract_values_with_xpath(
            response, '//div[contains(@class, "main_holder")]//div[contains(@class, "homepage")]/ul/li/a/@href')
        for relative_url in deals:
            url = response.urljoin(relative_url)
            self.log("Deal url: %s" % url)
            yield self.create_request(url, self.parse_today_deals_list)

        # Side Bar Deals
        deals = extract_values_with_xpath(
            response, '//ul[@class="sidenav"]/li/a[contains(@class, "sidetab-daily-deals")]/@href')
        for relative_url in deals:
            url = response.urljoin(relative_url)
            self.log("Deal url: %s" % url)
            yield self.create_request(url, self.parse_today_deals_list)

    def parse_today_deals_list(self, response):
        # Alternative solution:
        # Use selenium to scroll down the page
        # chrome.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        script_content = extract_first_value_with_xpath(
            response, '//div[@id="menu"]/script[contains(text(), ".countdown")]/text()')
        start_time, end_time = None, None
        if script_content is not None:
            matched = re.search(r'\.countdown\(([0-9]+)\)', script_content)
            if matched:
                countdown = matched.groups()[0]
                start_time, end_time = self.__class__.get_daily_deal_utc_time_from_countdown(countdown)
                self.log('Found count down timer {0}. Start: {1}, End: {2}'.format(countdown, start_time, end_time))
        if start_time is None:
            start_time, end_time = self.__class__.get_daily_deal_utc_time()
        index = 0
        for deal_elem in response.xpath('//ul[@class="catalogue"]/li'):
            index += 1
            # noinspection PyBroadException
            try:
                deal = self.parse_today_deal(response, deal_elem, start_time, end_time)
            except:
                deal = None
                self.log("Failed to parse deal {0} in {1}\n"
                         "Error: {2}".format(index, response.url, traceback.format_exc()))
            if deal is None:
                continue
            yield deal

    def parse_today_deal(self, response, deal_elem, start_time, end_time):
        soldout = deal_elem.xpath('./div[@class="sold_home_product"]')
        if len(soldout) > 0:
            # Deal is already sold out.
            return None
        deal_summary_elem = first_elem_with_xpath(deal_elem, './a')
        relative_url = extract_first_value_with_xpath(deal_summary_elem, './@href')
        url = response.urljoin(relative_url)
        deal = ProductItem()
        deal['retailer'] = self.retailer
        deal['store'] = self.store
        deal['landing_page'] = url
        deal['title'] = extract_first_value_with_xpath(deal_summary_elem, './div[@class="title"]/h2/text()')
        deal['description'] = extract_first_value_with_xpath(deal_summary_elem, './div[@class="title"]/h3/text()')
        price_elem = deal_summary_elem.xpath('./div[@class="price"]//span[@class="amount"]')
        amount = extract_first_value_with_xpath(price_elem, './text()')
        decimal_amount = extract_first_value_with_xpath(price_elem, './span/text()')
        price = amount + (decimal_amount if decimal_amount is not None else '')
        deal['price'] = sanitize_price(price)
        deal['unit'] = ''
        saved = extract_first_value_with_xpath(deal_summary_elem, './div[@class="save day_colour"]/text()')
        if not saved:
            saved = extract_first_value_with_xpath(deal_summary_elem, './div[@class="why-pay"]/text()')
        deal['saved'] = saved

        deal['promotion_start_date'] = start_time
        deal['promotion_end_date'] = end_time
        image_src = extract_first_value_with_xpath(deal_summary_elem,
                                                   './div[@class="image"]/img/@src')
        if image_src is None:
            # Lazy loading url
            image_src = extract_first_value_with_xpath(deal_summary_elem,
                                                       './div[@class="image"]/img/@data-src')
        if image_src is None:
            # Can't get deal image, go to deal detail page
            return self.create_request(url, self.parse_deal_details, meta={'deal': deal})
        else:
            image_src = response.urljoin(image_src)
            self._create_or_update_deal_in_db(deal, image_src)
            return deal

    def parse_deal_details(self, response):
        deal = response.meta['deal']
        image_src = \
            extract_first_value_with_xpath(
                response,
                '//div[contains(@class, "product-details")]//img[@itemprop="image"]/@src')
        # We currently only need image thumbnail.
        image_src = image_src.replace('_large', '_small')
        self._create_or_update_deal_in_db(deal, image_src)
        yield deal

    def _create_or_update_deal_in_db(self, deal, image_src):
        db_deal = self._get_prod(deal['landing_page'])
        if db_deal is None:
            db_deal = deal.save()
        else:
            db_deal.title = deal['title']
            db_deal.description = deal['description']
            db_deal.price = deal['price']
            db_deal.unit = deal['unit']
            db_deal.saved = deal['saved']
            db_deal.promotion_start_date = deal['promotion_start_date']
            db_deal.promotion_end_date = deal['promotion_end_date']
            db_deal.landing_page = deal['landing_page']
            db_deal.active = True
            db_deal.save()
        self._add_or_update_prod(db_deal)
        if not db_deal.product_images.filter(original_url=image_src).exists():
            # TODO: Hash
            unique_hash = str(datetime.utcnow().timestamp())
            db_deal.product_images.create(unique_hash=unique_hash,
                                          original_url=image_src)
        return db_deal

    @classmethod
    def get_daily_deal_utc_time(cls):

        # Deal ends at 12 PM every day in nz time,
        now = datetime.utcnow()
        start_time = datetime(year=now.year, month=now.month, day=now.day,
                              hour=23, minute=0, second=0)
        end_time = start_time
        # TODO: consider daylight saving time
        if now.hour < 23:
            end_time = datetime(year=now.year, month=now.month, day=now.day,
                                hour=23, minute=0, second=0) + timedelta(days=1)
        else:
            start_time = datetime(year=now.year, month=now.month, day=now.day,
                                  hour=23, minute=0, second=0) - timedelta(days=1)
        return int(start_time.timestamp()), int(end_time.timestamp())

    @classmethod
    def get_daily_deal_utc_time_from_countdown(cls, countdown):
        # Convert to seconds
        if isinstance(countdown, str):
            countdown = float(countdown) / 1000.0
        elif isinstance(countdown, (int, float)):
            countdown /= 1000.0
        now = datetime.utcnow()
        # This is daily deals, max countdown is one day, 86400 secs
        start_time = now - timedelta(seconds=(86400.0 - countdown))
        end_time = start_time + timedelta(days=1)
        return int(start_time.timestamp()), int(end_time.timestamp())

