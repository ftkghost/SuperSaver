from django.db import models

from country.models import Country


class DataSource (models.Model):
    id = models.SmallIntegerField(primary_key=True, serialize=False, verbose_name='ID')
    # Normalised name in lower case
    name = models.CharField(max_length=256, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=256, null=False, blank=False)
    site = models.URLField(max_length=256, null=False, blank=False)
    logo_url = models.URLField(max_length=256, null=True, blank=False)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=False, related_name='datasources')

    def save(self, **kwargs):
        self.name = self.name.lower()
        super().save(**kwargs)

    def __repr__(self):
        return 'DataSource: id={0}, name={1}, display_name={2}, site={3}, logo={4}, country={5}' \
            .format(self.id, self.name, self.display_name,
                    self.site, self.logo_url, self.country_id)

