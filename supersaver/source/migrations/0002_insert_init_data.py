# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from supersaver.constants import *


def init_data(apps, schema_editor):
    my_model = apps.get_model("source", "DataSource")
    db_alias = schema_editor.connection.alias

    country_model = apps.get_model("country", "Country")
    nz_country = country_model.objects.using(db_alias).get(country_code='NZ')
    my_model.objects.using(db_alias).bulk_create([
        my_model(id=DATASOURCE_ID_1_DAY_CO_NZ,
                 name=DATASOURCE_NAME_1_DAY_CO_NZ,
                 display_name='1-day.co.nz',
                 site='https://www.1-day.co.nz',
                 logo_url=None,
                 country=nz_country),
        my_model(id=DATASOURCE_ID_GRABONE_CO_NZ,
                 name=DATASOURCE_NAME_GRABONE_CO_NZ,
                 display_name='GrabOne',
                 site='https://grabone.co.nz',
                 logo_url=None,
                 country=nz_country),
        my_model(id=DATASOURCE_ID_LASOO_CO_NZ,
                 name=DATASOURCE_NAME_LASOO_CO_NZ,
                 display_name='Lasoo',
                 site='https://www.lasoo.co.nz',
                 logo_url=None,
                 country=nz_country),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('source', '0001_initial'),
        ('country', '0002_insert_init_data'),
    ]

    operations = [
        migrations.RunPython(init_data)
    ]
