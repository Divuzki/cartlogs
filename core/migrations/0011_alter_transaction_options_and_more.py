# Generated by Django 5.1.6 on 2025-02-27 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_wallet_balance'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_gateway',
            field=models.CharField(choices=[('unknown', 'Unknown'), ('paystack', 'Paystack'), ('flutterwave', 'Flutterwave'), ('wallet', 'Wallet'), ('manual', 'Manual Transfer')], default='unknown', editable=False, max_length=20),
        ),
    ]
