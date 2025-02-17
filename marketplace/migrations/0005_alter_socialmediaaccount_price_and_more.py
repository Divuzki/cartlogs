# Generated by Django 5.1.6 on 2025-02-16 23:05

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0004_remove_socialmediaaccount_tweet_count_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='price',
            field=models.DecimalField(decimal_places=2, help_text='The price of the account. It is in Naira.', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='verification_status',
            field=models.CharField(max_length=12),
        ),
        migrations.DeleteModel(
            name='PriceHistory',
        ),
    ]
