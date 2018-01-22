from supersaver.constants import RETAILER_FRESH_CHOICE

from dealcrawler.util import *
from dealcrawler.model.items import ProductItem

from .SpecialDealAllStoresSiteSpider import SpecialDealAllStoresSiteSpider


class FreshChoiceSpecialDealSpider(SpecialDealAllStoresSiteSpider):
    name = "freshchoice.co.nz"
    catalogue_list_url = "http://catalogues.freshchoice.co.nz/data.js?type=contentloader" \
                         "&url=%2Fhome.html%3Ffragment%3Dembed"
    catalogue_base_url = "http://catalogues.freshchoice.co.nz/"
    region_url = "http://freshchoice.co.nz/stores"
    store_url = "http://freshchoice.co.nz/index.php?option=com_storelocator" \
                "&view=map&format=raw&searchall=1&Itemid=136&catid=-1&tagid=-1&featstate=0"

    def __init__(self, *args, **kwargs):
        super().__init__(
            RETAILER_FRESH_CHOICE,
            self.__class__.store_url,
            self.__class__.region_url,
            *args, **kwargs)

    # http://catalogues.freshchoice.co.nz/data.js?type=search&
    # isn={0}&ipp=40&pc=1023&fragment=embed&jsonp=mf{1}
    # "Host": "catalogues.freshchoice.co.nz",
    #"Referer": "http://freshchoice.co.nz/savings",
    #"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36",

    def create_or_update_product(self, response):
        for item_elem in response.xpath('//ul[@class="product-view-list list"]/li/article'):
            product_url = item_elem.extract_first_value_with_xpath('@data-url')
            product_image = item_elem.extract_first_value_with_xpath('./div[contains(@class, "offer-image")]/img/@src')

            item = ProductItem()
            item['description'] = description

            price_and_unit = item_elem.extract_first_value_with_xpath('./div/span[contains(@class, "product_price")]')

            item['price'] = price
            item['unit'] = unit
            item['remark'] = ''
            item['promotion_start_date'] = start_date
            item['promotion_end_date'] = end_date
            item['category'] = cat
            item['store'] = None
            # Update ready to true only if product image downloaded
            item['ready'] = False
            item['retailer'] = self.retailer
            item['active'] = True

            pass

