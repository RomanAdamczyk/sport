# Generated by Django 5.1 on 2024-09-21 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0002_rename_staduim_team_stadium'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='stadium',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
