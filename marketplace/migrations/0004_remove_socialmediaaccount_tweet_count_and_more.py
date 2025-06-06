# Generated by Django 5.1.6 on 2025-02-16 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0003_remove_cartsession_user_socialmediaaccount_image_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialmediaaccount',
            name='tweet_count',
        ),
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='description',
            field=models.TextField(help_text='A brief description of the social media account.'),
        ),
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='followers_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='following_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
