# Generated by Django 3.1.3 on 2021-03-13 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0030_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='cheating_checking',
            field=models.BooleanField(default=False),
        ),
    ]