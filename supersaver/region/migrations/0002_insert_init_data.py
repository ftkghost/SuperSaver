# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from supersaver.constants import *
from supersaver.settings import make_internal_property_name


def init_data(apps, schema_editor):
    region_model = apps.get_model("region", "Region")
    db_alias = schema_editor.connection.alias

    country_model = apps.get_model("country", "Country")
    nz_country = country_model.objects.using(db_alias).get(country_code='NZ')
    db_model = region_model.objects.using(db_alias)

    def create_row(display_name, parent=None):
        return db_model.create(name=display_name.lower(),
                               display_name=display_name,
                               parent=parent,
                               country=nz_country)

    def bulk_create_rows(name_parent_pairs):
        models = [region_model(name=n.lower(), display_name=n, parent=p, country=nz_country) for n, p in name_parent_pairs]
        db_model.bulk_create(models)

    all_nz = create_row("All New Zealand")
    north_island = create_row('North Island', all_nz)
    south_island = create_row('South Island', all_nz)
    bulk_create_rows([
        # North Island Regions
        ("Auckland", north_island),
        ("Waikato", north_island),
        ("Northland", north_island),
        ("Wellington", north_island),
        ("Manawatu - Wanganui", north_island),
        ("Tauranga", north_island),
        ("Rotorua - Taupo", north_island),
        ("Hawkes Bay", north_island),
        ("Taranaki", north_island),
        # South Island Regions
        ("Christchurch", south_island),
        ("Nelson - Marlborough", south_island),
        ("Queenstown - Wanaka", south_island),
        ("Dunedin - Invercargill", south_island),
        ("Stewart Island", south_island),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('region', '0001_initial'),
        ('country', '0002_insert_init_data'),
    ]

    operations = [
        migrations.RunPython(init_data)
    ]
