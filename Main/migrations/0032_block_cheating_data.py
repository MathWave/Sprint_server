# Generated by Django 3.1.3 on 2021-03-14 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0031_block_cheating_checking'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='cheating_data',
            field=models.TextField(default='[]'),
        ),
    ]