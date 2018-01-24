# Generated by Django 2.0.1 on 2018-01-23 22:23

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0001_initial'),
        ('retailer', '0001_initial'),
        ('category', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=512)),
                ('price', models.DecimalField(decimal_places=2, max_digits=11)),
                ('unit', models.CharField(blank=True, max_length=32)),
                ('saved', models.CharField(max_length=64, null=True)),
                ('landing_page', models.CharField(db_index=True, max_length=512)),
                ('fast_buy_link', models.CharField(db_index=True, max_length=512, null=True)),
                ('promotion_start_date', models.PositiveIntegerField()),
                ('promotion_end_date', models.PositiveIntegerField()),
                ('ready', models.BooleanField(default=False)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('categories', models.ManyToManyField(related_name='_product_categories_+', to='category.Category')),
                ('retailer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='retailer.Retailer')),
                ('store', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='store.Store')),
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
    ]
