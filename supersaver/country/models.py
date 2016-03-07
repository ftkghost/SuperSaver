from django.db import models


class Country(models.Model):
    """
    Country
    """
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=64, null=False, blank=False)
    country_code = models.CharField(max_length=2, null=False, blank=False, db_index=True)

    def __repr__(self):
        return "Country: id={0}, name={1}, code={2}".format(self.id, self.name, self.country_code)
