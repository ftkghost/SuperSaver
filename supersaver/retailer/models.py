from django.db import models
from supersaver.constants import *
from country.models import Country
from source.models import DataSource
from common.property import Property


class Retailer (models.Model):
    # Normalised name in lower case
    name = models.CharField(max_length=256, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=256, null=False, blank=False)
    site = models.URLField(max_length=256, null=True, blank=False)
    logo_url = models.URLField(max_length=256, null=True, blank=False)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=False, related_name='retailers')
    datasource = models.ForeignKey(DataSource, on_delete=models.PROTECT, null=False, related_name='retailers')

    def save(self, **kwargs):
        self.name = self.name.lower()
        super().save(**kwargs)

    def __repr__(self):
        return 'Retailer: id={0}, name={1}, display_name={2}, site={3}, logo={4}, country={5}, datasource={6}'\
            .format(self.pk, self.name, self.display_name,
                    self.site, self.logo_url, self.country_id, self.datasource_id)


class RetailerProperty (Property):
    """
    Retailer property bag.
    """
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, null=False, related_name='properties')

    def __repr__(self):
        return 'RetailerProperty: id={0}, retailer={1}, name={2}, value={3}'.format(
            self.pk,
            self.retailer_id,
            self.name,
            self.value
        )
