# Generated by Django 4.2.20 on 2025-05-31 16:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0028_alter_category_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['position'], 'verbose_name_plural': 'Categories'},
        ),
    ]
