# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from supersaver.constants import *


def init_data(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    retailer_model = apps.get_model("retailer", "Retailer")
    one_day_retailer = retailer_model.objects.using(db_alias).get(name=RETAILER_NAME_1_DAY_CO_NZ)

    region_model = apps.get_model("region", "Region")
    nz_region = region_model.objects.using(db_alias).get(name='all new zealand')

    store_model = apps.get_model("store", "Store")
    store_model.objects.using(db_alias).bulk_create([
        store_model(
            retailer=one_day_retailer,
            region=nz_region,
            name='1-day online',
            tel=None,
            address='152 Collins Road, Hamilton 3206, New Zealand',
            website=None,
            email=None,
            working_time='09:00 - 18:00 Monday-Thursday\n09:00 - 17:00 Friday',
            longitude=175.268416,
            latitude=-37.820279,
            active=True),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
        ('retailer', '0002_insert_init_data'),
    ]

    operations = [
        migrations.RunPython(init_data)
    ]
