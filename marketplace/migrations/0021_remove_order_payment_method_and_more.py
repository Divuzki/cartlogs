# Generated by Django 5.1.6 on 2025-02-23 10:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_transaction_payment_gateway_and_more'),
        ('marketplace', '0020_alter_socialmediaaccount_social_media'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='payment_method',
        ),
        migrations.RemoveField(
            model_name='order',
            name='payment_reference',
        ),
        migrations.RemoveField(
            model_name='order',
            name='payment_status',
        ),
        migrations.AddField(
            model_name='order',
            name='transaction',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.transaction'),
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
    ]
