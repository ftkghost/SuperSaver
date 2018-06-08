from django.db import models


class Property (models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    value = models.CharField(max_length=1024, null=False, blank=True)

    INTERNAL_PROPERTY_PREFIX = '__'

    class Meta:
        abstract = True

    @classmethod
    def get_public_properties(cls, **kwargs):
        return cls.objects.exclude(name__startswith=cls.INTERNAL_PROPERTY_PREFIX).filter(**kwargs)

    @classmethod
    def get_internal_properties(cls, **kwargs):
        return cls.objects.filter(name__startswith=cls.INTERNAL_PROPERTY_PREFIX, **kwargs)

    def value_equals_to(self, other):
        if other is not Property:
            return False
        return self.name == other.name \
               and self.value == other.value

    def __repr__(self):
        return '<Property: id={0}, name={1}, value={2}>' \
            .format(self.pk, self.name, self.value)

