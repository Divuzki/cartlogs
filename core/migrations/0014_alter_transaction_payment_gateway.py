# Generated by Django 5.1.6 on 2025-04-09 02:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_transaction_type_alter_transaction_wallet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='payment_gateway',
            field=models.CharField(choices=[('unknown', 'Unknown'), ('korapay', 'Korapay'), ('etegram', 'Etegram'), ('wallet', 'Wallet'), ('manual', 'Manual Transfer')], default='unknown', max_length=20),
        ),
    ]
