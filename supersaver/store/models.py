from django.db import models
from uuid import uuid4

from region.models import Region
from retailer.models import Retailer
from common.models import Property


class Store(models.Model):
    """
    Stores
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    retailer = models.ForeignKey(Retailer, on_delete=models.PROTECT, null=False, related_name='stores')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=False, related_name='stores')
    name = models.CharField(max_length=256, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=256, null=False, blank=False)
    tel = models.CharField(max_length=32, null=True, blank=False)
    address = models.CharField(max_length=512, null=True, blank=False)
    working_hours = models.CharField(max_length=512, null=True, blank=False)
    website = models.CharField(max_length=512, null=True, blank=False)
    email = models.CharField(max_length=128, null=True, blank=False)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    active = models.BooleanField(default=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def save(self, **kwargs):
        self.name = self.name.lower()
        super().save(**kwargs)

    def value_equals_to(self, other):
        if other is not Store:
            return False
        return self.name == other.name \
            and self.longitude == other.longitude \
            and self.latitude == other.latitude \
            and self.address == other.address

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


class StoreProperty (Property):
    """
    Store property bag.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=False, related_name='properties')

    def __repr__(self):
        return 'StoreProperty: id={0}, store={1}, name={2}, value={3}'.format(
            self.pk,
            self.store_id,
            self.name,
            self.value
        )
