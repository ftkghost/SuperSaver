# Generated by Django 2.0.1 on 2018-06-06 05:55

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('category', '0001_initial'),
        ('retailer', '0002_insert_init_data'),
        ('store', '0002_insert_init_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('description', models.CharField(blank=True, default='', max_length=512)),
                ('price', models.DecimalField(decimal_places=2, max_digits=11)),
                ('unit', models.CharField(blank=True, default='', max_length=32)),
                ('saved', models.CharField(default=None, max_length=64, null=True)),
                ('landing_page', models.CharField(db_index=True, max_length=512)),
                ('fast_buy_link', models.CharField(default=None, max_length=512, null=True)),
                ('promotion_start_date', models.PositiveIntegerField()),
                ('promotion_end_date', models.PositiveIntegerField()),
                ('ready', models.BooleanField(default=False)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('search_vector', django.contrib.postgres.search.SearchVectorField()),
                ('categories', models.ManyToManyField(related_name='_product_categories_+', to='category.Category')),
                ('retailer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='retailer.Retailer')),
                ('source_categories', models.ManyToManyField(related_name='_product_source_categories_+', to='category.SourceCategory')),
                ('stores', models.ManyToManyField(related_name='products', to='store.Store')),
            ],
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_hash', models.CharField(max_length=64, unique=True)),
                ('original_url', models.CharField(max_length=512)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_images', to='product.Product')),
            ],
        ),
        migrations.CreateModel(
            name='ProductProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('value', models.CharField(blank=True, max_length=1024)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='properties', to='product.Product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector'], name='product_search_index'),
        ),
    ]
