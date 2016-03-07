from django.db import models

from supersaver.constants import DEVICE_TYPE_ANDROID, DEVICE_TYPE_IOS, DEVICE_TYPE_WINPHONE

DEVICE_TYPES = (
    (DEVICE_TYPE_ANDROID, "android"),
    (DEVICE_TYPE_IOS, "ios"),
    (DEVICE_TYPE_WINPHONE, "winphone")
)


class Device(models.Model):
    """
    Use device to support push notification and identification.
    """
    name = models.CharField(max_length=64, null=True, blank=False)
    type = models.SmallIntegerField(choices=DEVICE_TYPES, null=False)
    brand = models.CharField(max_length=128, null=True, blank=False)
    model = models.CharField(max_length=128, null=True, blank=False)
    os_version = models.CharField(max_length=128, null=True, blank=False)
    token = models.CharField(max_length=128, unique=True, null=False, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return u'id={0}, type={1}, token={2}'.format(self.pk, DEVICE_TYPES[self.type][1], self.token)
