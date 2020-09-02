# Generated by Django 3.1 on 2020-09-01 08:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Main', '0011_auto_20200814_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='weight',
            field=models.FloatField(default=1.0),
        ),
        migrations.CreateModel(
            name='ExtraFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Main.task')),
            ],
        ),
    ]