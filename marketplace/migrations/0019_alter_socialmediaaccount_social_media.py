# Generated by Django 5.1.6 on 2025-02-22 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0018_alter_socialmediaaccount_social_media'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='social_media',
            field=models.CharField(choices=[('OJ’s SPECIAL STOCK🌚💯', 'OJ’s SPECIAL STOCK🌚💯'), ('texting', 'Texting💬'), ('twitter', 'Twitter'), ('facebook', 'Facebook'), ('instagram', 'Instagram'), ('snapchat', 'Snapchat'), ('reddit', 'Reddit'), ('tiktok', 'TikTok'), ('vpn', 'VPN'), ('tools', 'Tools'), ('email', 'Email'), ('streaming', 'Streaming'), ('others', 'Others')], max_length=20),
        ),
    ]
