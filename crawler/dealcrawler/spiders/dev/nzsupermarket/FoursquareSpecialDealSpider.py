import scrapy
from retailer.models import Retailer
from supersaver.constants import RETAILER_FOURSQUARE


class FoursquareSpecialDealSpider(scrapy.Spider):
    # retailer_model(name="Foursquare",
    #                type=0,
    #                site="http://www.foursquare.co.nz",
    #                deals_url="http://www.foursquare.co.nz/promotions-competitions/"),
    name = "foursquare.co.nz"

    def __init__(self, *args, **kwargs):
        super(FoursquareSpecialDealSpider, self).__init__(*args, **kwargs)
        self.retailer = Retailer.objects.get(id=RETAILER_FOURSQUARE)
        # http://www.foursquare.co.nz/promotions-competitions/

    def parse(self, response):
        pass

