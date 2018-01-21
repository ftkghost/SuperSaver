__author__ = 'qinpeng'

from decimal import Decimal

from supersaver.constants import RETAILER_SUPERVALUE
from category.models import Category

from dealcrawler.util import *
from dealcrawler.model.items import ProductItem
from product.models import Product

from .SpecialDealAllStoresSiteSpider import SpecialDealAllStoresSiteSpider


class SuperValueSpecialDealSpider(SpecialDealAllStoresSiteSpider):
    name = "supervalue.co.nz"

    store_list_url = "http://supervalue.co.nz/index.php?option=com_storelocator" \
                     "&view=map&format=raw&searchall=1&Itemid=136&catid=-1&tagid=-1&featstate=0"
    region_url = "http://supervalue.co.nz/stores"

    def __init__(self, *args, **kwargs):
        super(SuperValueSpecialDealSpider, self).__init__(
            RETAILER_SUPERVALUE,
            self.__class__.store_list_url,
            self.__class__.region_url,
            *args, **kwargs)

    def create_or_update_categories(self, selector):
        categories = Category.objects.filter(active=True)
        category_by_name = {c.name.lower(): c for c in categories}
        category_by_css = {}
        for option in selector.xpath('//select[@name="category"]/option'):
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
            category_by_css[category_css_name] = cat
        self.category_by_css = category_by_css

    def create_or_update_products(self, response):
        # Create/Update special price products.
        for week_tab in response.css('.week-tab'):
            week_date_range_str = week_tab.extract_first_value_with_xpath('./h3/text()')
            start_date, end_date = self.__class__.parse_date_range(week_date_range_str)
            products = Product.objects.filter(retailer=self.retailer,
                                              promotion_start_date__gte=start_date, promotion_end_date__lte=end_date)
            product_by_description = {p.description: p for p in products}
            self.log(u'Weely special deals: {0} - {1}'.format(start_date, end_date))
            for prod_node in week_tab.css('.row').xpath('./div'):
                css_classes = prod_node.extract_first_value_with_xpath('./@class').split(' ')
                cat = None
                # Usually the category css is the last one, but in case there is something changed,
                # we check all css until find the category css.
                for i in range(len(css_classes)-1, -1, -1):
                    cls_name = css_classes[i]
                    cat_css_name = cls_name.split('-')[-1]
                    if cat_css_name in self.category_by_css:
                        cat = self.category_by_css[cat_css_name]
                        break
                img = prod_node.extract_first_value_with_xpath('./div/img/@src')
                description = prod_node.extract_first_value_with_xpath('./h3/text()')
                size = prod_node.extract_first_value_with_xpath('./p[@class="size"]/text()')
                if size is not None:
                    description = u'{0} ({1})'.format(description, size)
                price_node = prod_node.xpath('./p[@class="price"]')[0]
                price = price_node.extract_first_value_with_xpath('./text()')
                # Transfer price from cent to dollar if necessary
                price = Decimal((price[0:-1])/100.0 if price.endswith('c') else Decimal(price))
                unit = price_node.xpath('./sub/text()').extract()[-1].strip()
                remark = prod_node.extract_first_value_with_xpath('./p[@class="inclusions-exclusions"]/text()')
                remark = None if remark == u'' else remark
                item = ProductItem()
                item['description'] = description
                item['price'] = price
                item['unit'] = unit
                item['remark'] = remark
                item['promotion_start_date'] = start_date
                item['promotion_end_date'] = end_date
                item['category'] = cat
                item['store'] = None
                # Update ready to true only if product image downloaded
                item['ready'] = False
                item['retailer'] = self.retailer
                item['active'] = True
                if description in product_by_description:
                    # Update existing prod
                    prod = product_by_description.pop(description)
                    self.__class__.update_product(prod, item)
                else:
                    # New prod
                    prod = item.save()
                yield item
            for prod in product_by_description.values():
                # These product are no longer in weekly special deal list.
                self.log(u'Delete product ({0}): {1}'.format(prod.id, prod.description))
                prod.active = False
                prod.save()
