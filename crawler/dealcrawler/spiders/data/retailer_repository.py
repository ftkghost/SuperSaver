# -*- coding: utf-8 -*-

from dealcrawler.common.repository import Repository
from retailer.models import Retailer


class RetailerRepository (Repository):

    def __init__(self, datasource, country, retailers):
        super().__init__(retailers, lambda r: r.r.name)
        self.datasource = datasource
        self.country = country

    def add_or_update_retailer_in_db(self, retailer_name, logo_url=None, properties=None):
        """
        Create or update retailer in database and update repository memory store.

        :param retailer_name:
        :param logo_url:
        :param properties:
        :return:
        """
        retailer = self.get_item(retailer_name)
        if retailer is None:
            retailer = Retailer()
            retailer.name = retailer_name.lower()
            retailer.display_name = retailer_name
            retailer.logo_url = logo_url
            retailer.datasource = self.datasource
            retailer.country = self.country
            retailer.save()
            self.add_or_update_item(retailer)
        if properties:
            self.__class__._update_retailer_props_in_db(retailer, properties)
        return retailer

    @staticmethod
    def _update_retailer_props_in_db(retailer, properties):
        ex_props = list(retailer.properties.all())
        for prop in properties:
            found = None
            for ex_prop in ex_props:
                if ex_prop.value_equals_to(prop):
                    found = ex_prop
            if not found:
                prop.retailer = retailer
                prop.save()
            else:
                ex_props.remove(found)
        for p in ex_props:
            p.delete()
