# Generated by Django 3.1.3 on 2020-12-26 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0026_block_show_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='mark_formula',
            field=models.TextField(default='None'),
        ),
    ]