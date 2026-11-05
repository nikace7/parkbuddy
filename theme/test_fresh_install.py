"""A fresh database must match the models and serve the home page.

Run with: python manage.py test theme
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from theme.models import ParkingSpace


class FreshInstallTests(TestCase):
    def test_migrations_cover_every_model_change(self):
        # Exits non-zero if the models have drifted from theme/migrations.
        call_command('makemigrations', check=True, dry_run=True, interactive=False, stdout=StringIO())

    def test_home_page_serves_an_empty_database(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_pages_serve_a_space_without_images(self):
        user = get_user_model().objects.create(username='manager')
        space = ParkingSpace.objects.create(
            user=user,
            location='SRID=4326;POINT(85.324 27.7172)',
            vehicle_type='Car',
            location_name='New Road',
            price_per_hr=50,
            price_per_half_hr=30,
            info='No photos uploaded yet',
        )
        self.assertEqual(self.client.get('/').status_code, 200)

        self.client.force_login(user)
        self.assertEqual(self.client.get(f'/book/{space.id}/').status_code, 200)
