# Generated by Django 5.1 on 2024-12-12 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('football', '0003_alter_team_stadium'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('birth_day', models.DateField()),
                ('position', models.CharField(choices=[('gk', 'goalkeeper'), ('df', 'defender'), ('mf', 'midfielder'), ('st', 'striker')], max_length=2)),
                ('date_in', models.DateField(blank=True)),
                ('date_out', models.DateField(blank=True)),
                ('nationality', models.CharField(max_length=40)),
                ('team', models.ManyToManyField(blank=True, to='football.team')),
            ],
        ),
    ]
