# Generated by Django 4.2.20 on 2025-05-04 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0022_log_order_item'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='social_media',
            field=models.CharField(choices=[('instagram', 'Instagram'), ('facebook', 'Facebook'), ('tiktok', 'TikTok'), ('twitter', 'Twitter'), ('vpn', 'VPN'), ('OJ’s SPECIAL STOCK🌚💯', 'OJ’s SPECIAL STOCK🌚💯'), ('email', 'Email'), ('streaming', 'Streaming'), ('Texting💬', 'Texting💬'), ('snapchat', 'Snapchat'), ('reddit', 'Reddit'), ('tools', 'Tools'), ('others', 'Others')], max_length=20),
        ),
    ]
