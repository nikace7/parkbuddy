# Generated by Django 5.1.1 on 2024-10-02 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("theme", "0003_delete_markerpoint"),
    ]

    operations = [
        migrations.AddField(
            model_name="parkingspace",
            name="name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]