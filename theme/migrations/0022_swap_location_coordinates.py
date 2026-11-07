from django.db import migrations

# Spaces were saved as (latitude, longitude), so the search measured them from the
# wrong place on the globe. A row with |x| > 90 cannot be in that order, because x
# would be a latitude, so it stays as it is. Swapping twice restores the original,
# so the same statement reverses it.
SWAP = """
    UPDATE theme_parkingspace
    SET location = ST_FlipCoordinates(location::geometry)::geography
    WHERE abs(ST_X(location::geometry)) <= 90
"""


class Migration(migrations.Migration):

    dependencies = [
        ("theme", "0021_parkingslot_is_disabled"),
    ]

    operations = [
        migrations.RunSQL(SWAP, SWAP),
    ]
