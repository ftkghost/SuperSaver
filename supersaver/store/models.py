from django.db import models

from region.models import Region
from retailer.models import Retailer


class Store(models.Model):
    """
    Stores
    """
    retailer = models.ForeignKey(Retailer, null=False, related_name='stores')
    region = models.ForeignKey(Region, null=False, related_name='stores')
    name = models.CharField(max_length=256, null=False, blank=False)
    tel = models.CharField(max_length=32, null=True, blank=False)
    address = models.CharField(max_length=512, null=True, blank=False)
    working_time = models.CharField(max_length=512, null=True, blank=False)
    website = models.CharField(max_length=512, null=True, blank=False)
    email = models.CharField(max_length=128, null=True, blank=False)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    active = models.BooleanField(default=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def save(self, **kwargs):
        self.name = self.name.lower()
        super(Store, self).save(**kwargs)

    def __repr__(self):
        return "Store: id={0}, " \
               "retailer={1}, region={2}, " \
               "name={3}, tel={4}" \
               "location=({5}, {6}), " \
               "website={7}, " \
               "email={8}, " \
               "address={9}, active={10}".format(self.pk,
                                                 self.retailer_id, self.region_id,
                                                 self.name, self.tel,
                                                 self.latitude, self.longitude,
                                                 self.website,
                                                 self.email,
                                                 self.address, self.active)
