# Generated by Django 5.1.6 on 2025-02-23 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_transaction_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='payment_reference',
            field=models.CharField(blank=True, editable=False, max_length=100, null=True, unique=True),
        ),
    ]
