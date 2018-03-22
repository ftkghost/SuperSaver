# -*- coding: utf-8 -*-

from dealcrawler.common.repository import Repository
from retailer.models import Retailer


class RetailerRepository (Repository):

    def __init__(self, datasource, country):
        self.datasource = datasource
        self.country = country
        retailers = datasource.retailers.all()
        super().__init__(retailers, lambda r: r.name)

    def get_retailer_by_name(self, name):
        if not name:
            return None
        return self.get_item(name.lower())

    def add_or_update_retailer_in_db(self, retailer_name, website=None, logo_url=None, properties=None):
        """
        Create or update retailer in database and update repository memory store.

        :param retailer_name:
        :param logo_url:
        :param properties:
        :return:
        """
        normalized_retailer_name = retailer_name.lower()
        retailer = self.get_item(normalized_retailer_name)
        if retailer is None:
            retailer = Retailer()
        retailer.name = normalized_retailer_name
        retailer.display_name = retailer_name
        retailer.site = website
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
                if ex_prop.name == prop.name:
                    found = ex_prop
                    break
            if not found:
                # Create new props
                prop.retailer = retailer
                prop.save()
            else:
                if found.value != prop.value:
                    # Update existing props
                    found.value = prop.value
                    found.save()
                # Remove from pending deletion list
                ex_props.remove(found)
        # for p in ex_props:
        #     p.delete()
