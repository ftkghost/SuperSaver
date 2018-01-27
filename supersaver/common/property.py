from django.db import models


class Property (models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    value = models.CharField(max_length=1024, null=False, blank=True)

    class Meta:
        abstract = True

    def value_equals_to(self, other):
        if other is not Property:
            return False
        return self.name == other.name \
            and self.value == other.value

    def __repr__(self):
        return 'Property: id={0}, name={1}, value={2}'\
            .format(self.pk, self.name, self.value)
