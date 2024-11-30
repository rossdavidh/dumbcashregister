# Generated by Django 5.0.1 on 2024-07-02 22:29

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0006_company_currency_sym_company_price_divisor_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='price_divisor',
            field=models.DecimalField(decimal_places=10, default=Decimal('100'), max_digits=20, validators=[django.core.validators.MinValueValidator(1.0)]),
        ),
        migrations.AlterField(
            model_name='company',
            name='price_format',
            field=models.DecimalField(decimal_places=10, default=Decimal('2'), max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]