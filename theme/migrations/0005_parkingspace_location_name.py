# Generated by Django 5.1.1 on 2024-10-06 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("theme", "0004_parkingspace_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="parkingspace",
            name="location_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
