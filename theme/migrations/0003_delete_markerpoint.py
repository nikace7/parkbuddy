# Generated by Django 5.1.1 on 2024-10-01 09:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("theme", "0002_userprofile_delete_userotp"),
    ]

    operations = [
        migrations.DeleteModel(
            name="MarkerPoint",
        ),
    ]
