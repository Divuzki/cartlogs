# Generated by Django 5.1.6 on 2025-02-23 21:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_transaction_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallet',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0.0, editable=False, max_digits=10),
        ),
    ]
