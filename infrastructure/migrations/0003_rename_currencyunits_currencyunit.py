# Generated by Django 5.0.1 on 2024-02-12 19:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0002_currencyunits'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CurrencyUnits',
            new_name='CurrencyUnit',
        ),
    ]