# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from supersaver.constants import *
from supersaver.settings import make_internal_property_name


def init_data(apps, schema_editor):
    retailer_model = apps.get_model("retailer", "Retailer")
    db_alias = schema_editor.connection.alias

    country_model = apps.get_model("country", "Country")
    nz_country = country_model.objects.using(db_alias).get(country_code='NZ')
    source_model = apps.get_model("source", "DataSource")
    oneday_datasource = source_model.objects.using(db_alias).get(name=DATASOURCE_NAME_1_DAY_CO_NZ)
    lasoo_datasource = source_model.objects.using(db_alias).get(name=DATASOURCE_NAME_LASOO_CO_NZ)
    retailer_model.objects.using(db_alias).bulk_create([
        retailer_model(name=RETAILER_NAME_1_DAY_CO_NZ,
                       display_name='1-day.co.nz',
                       site='http://www.1-day.co.nz',
                       logo_url=None,
                       country=nz_country,
                       datasource=oneday_datasource),
        retailer_model(name=RETAILER_NAME_COUNTDOWN,
                       display_name='Countdown',
                       site='http://www.countdown.co.nz',
                       logo_url=None,
                       country=nz_country,
                       datasource=lasoo_datasource),
    ])

    countdown = retailer_model.objects.using(db_alias).get(name=RETAILER_NAME_COUNTDOWN)
    property_model = apps.get_model("retailer", "RetailerProperty")
    property_model.objects.using(db_alias).bulk_create([
        property_model(name=make_internal_property_name('lasoo_retailer_id'),
                       value='12698216709676',
                       retailer=countdown),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('retailer', '0001_initial'),
        ('source', '0002_insert_init_data'),
    ]

    operations = [
        migrations.RunPython(init_data)
    ]
