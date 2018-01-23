# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def init_data(apps, schema_editor):
    my_model = apps.get_model("currency", "Currency")
    db_alias = schema_editor.connection.alias

    currency_id = 1
    my_model.objects.using(db_alias).bulk_create([
        my_model(id=currency_id,
                 name="New Zealand Dollar",
                 currency_code='nzd',
                 sign='$')
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0001_initial'),
        ('country', '0002_insert_init_data'),
    ]

    operations = [
        migrations.RunPython(init_data)
    ]
