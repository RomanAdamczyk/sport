# Generated by Django 5.1 on 2024-12-17 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0004_player'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='date_in',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='date_out',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='position',
            field=models.CharField(choices=[('gk', 'bramkarz'), ('df', 'obrońca'), ('mf', 'pomocnik'), ('st', 'napastnik')], max_length=2),
        ),
    ]
