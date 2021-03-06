# Generated by Django 2.0.1 on 2018-01-26 05:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('country', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.SmallIntegerField(primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=256)),
                ('display_name', models.CharField(max_length=256)),
                ('site', models.URLField(max_length=256)),
                ('logo_url', models.URLField(max_length=256, null=True)),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='datasources', to='country.Country')),
            ],
        ),
    ]
