from django.db import models


class Category(models.Model):
    # Normalised name with lower case
    name = models.CharField(max_length=256, null=False, blank=False, db_index=True)
    display_name = models.CharField(max_length=256, null=False, blank=False)
    level = models.SmallIntegerField(null=False)
    active = models.BooleanField(default=True, null=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, default=None, related_name='subcategories')

    def __repr__(self):
        return "Category: id={0}, name={1}, display_name={2}, active={3}, parent={4}, level={5}"\
            .format(self.pk, self.name, self.display_name, self.active, self.parent_id, self.level)
