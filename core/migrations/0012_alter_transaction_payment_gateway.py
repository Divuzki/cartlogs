# Generated by Django 5.1.6 on 2025-03-11 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_transaction_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='payment_gateway',
            field=models.CharField(choices=[('unknown', 'Unknown'), ('paystack', 'Paystack'), ('flutterwave', 'Flutterwave'), ('wallet', 'Wallet'), ('manual', 'Manual Transfer')], default='unknown', max_length=20),
        ),
    ]
