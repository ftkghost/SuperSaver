from django.db import models
from source.models import DataSource


class Category(models.Model):
    # Normalised name with lower case
    name = models.CharField(max_length=256, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=256, null=False, blank=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, default=None, related_name='subcategories')
    active = models.BooleanField(default=True, null=False)

    def save(self, **kwargs):
        self.name = self.name.lower()
        super().save(**kwargs)

    def __repr__(self):
        return "Category: id={0}, name={1}, display_name={2}, active={3}, parent={4}" \
            .format(self.pk, self.name, self.display_name, self.active, self.parent_id)


class SourceCategory(models.Model):
    # Normalised name with lower case
    name = models.CharField(max_length=256, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=256, null=False, blank=False)
    active = models.BooleanField(default=True, null=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    source_category_id = models.CharField(max_length=64, null=True, blank=False)
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, null=False)

    def save(self, **kwargs):
        self.name = self.name.lower()
        super().save(**kwargs)

    def __repr__(self):
        return "SourceCategory: id={0}, name={1}, display_name={2}, active={3}, category={4}, " \
               "source_category_id={5}, source={6}" \
            .format(self.pk, self.name, self.display_name, self.active,
                    self.category_id, self.source_category_id, self.source_id)
