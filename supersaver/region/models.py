from django.db import models

from country.models import Country


class Region(models.Model):
    """
    Region in country.
    """
    name = models.CharField(max_length=128, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=128, null=False, blank=False)
    active = models.BooleanField(default=True, null=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, default=None, related_name='sub_regions')
    country = models.ForeignKey(Country, related_name='regions')

    def __repr__(self):
        return "Region: id={0}, " \
               "name={1}, " \
               "display_name={2}, " \
               "active={3}, " \
               "parent={4}, "\
               "country={5}".format(self.id, self.name, self.display_name,
                                    self.active, self.parent_id, self.country_id)

