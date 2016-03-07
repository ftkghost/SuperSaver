# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def init_data(apps, schema_editor):
    my_model = apps.get_model("country", "Country")
    db_alias = schema_editor.connection.alias

    country_id = 1
    my_model.objects.using(db_alias).bulk_create([
        my_model(id=country_id,
                 name="New Zealand",
                 country_code='NZ')
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(init_data)
    ]
