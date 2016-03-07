from django.db import models


class Property (models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    value = models.CharField(max_length=1024, null=False, blank=True)

    class Meta:
        abstract = True

    def __repr__(self):
        return 'Property: id={0}, name={1}, value={2}'\
            .format(self.pk, self.name, self.value)
