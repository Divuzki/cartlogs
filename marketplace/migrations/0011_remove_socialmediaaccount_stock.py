# Generated by Django 5.1.6 on 2025-02-19 16:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0010_log_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialmediaaccount',
            name='stock',
        ),
    ]
