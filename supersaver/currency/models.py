from django.db import models


class Currency(models.Model):
    """
    Currency
    """
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=64, null=False, blank=False)
    currency_code = models.CharField(max_length=4, null=False, blank=False, db_index=True)
    sign = models.CharField(max_length=4, null=False, blank=False)

    def __repr__(self):
        return "Currency: id={0}, name={1}, code={2}, sign={3}".format(self.id, self.name, self.currency_code, self.sign)
