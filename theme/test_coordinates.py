"""Locations are stored as (longitude, latitude), the order PostGIS expects."""
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from theme.models import ParkingSpace

LATITUDE, LONGITUDE = 27.7172, 85.324  # New Road, Kathmandu


class SavedSpaceTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create(username='manager'))
        with patch('theme.views.requests.get') as reverse_geocode:
            reverse_geocode.return_value.text = json.dumps({'address': {'suburb': 'New Road'}})
            self.client.post(reverse('save_parking_space'), {
                'parking_name': 'New Road Parking',
                'vehicle_type': 'Car',
                'latitude': LATITUDE,
                'longitude': LONGITUDE,
                'slots_count': 2,
                'price_per_hr': 50,
                'price_per_half_hr': 30,
                'info': 'Saved through the view',
            })
        self.space = ParkingSpace.objects.get()

    def search(self, latitude, longitude):
        response = self.client.get(reverse('search_nearest_parking'), {'latitude': latitude, 'longitude': longitude})
        self.assertEqual(response.json()['status'], 'success', response.content)
        return response.json()['data']

    def test_stored_as_longitude_then_latitude(self):
        self.assertEqual((self.space.location.x, self.space.location.y), (LONGITUDE, LATITUDE))

    def test_search_finds_it_within_1_km(self):
        # 0.005 degrees of latitude is about 554 m north.
        [found] = self.search(LATITUDE + 0.005, LONGITUDE)

        self.assertEqual(found['id'], self.space.id)
        self.assertAlmostEqual(found['distance'], 554, delta=5)
        self.assertEqual((found['latitude'], found['longitude']), (LATITUDE, LONGITUDE))

    def test_search_skips_it_beyond_1_km(self):
        # 0.05 degrees of latitude is about 5.5 km north.
        self.assertEqual(self.search(LATITUDE + 0.05, LONGITUDE), [])

    def test_home_map_gets_the_real_latitude_and_longitude(self):
        [marker] = json.loads(self.client.get('/').context['parking_spaces'])

        self.assertEqual((marker['latitude'], marker['longitude']), (LATITUDE, LONGITUDE))


class SwapMigrationTests(TestCase):
    AFTER_SWAP = '0022_swap_location_coordinates'

    def add_space(self, location):
        user, _ = get_user_model().objects.get_or_create(username='manager')
        return ParkingSpace.objects.create(
            user=user,
            location=location,
            vehicle_type='Car',
            location_name='New Road',
            price_per_hr=50,
            price_per_half_hr=30,
            info='Stored before the migration',
        )

    def test_swaps_old_rows_and_can_be_reversed(self):
        call_command('migrate', 'theme', '0021', verbosity=0)
        old_order = self.add_space(f'SRID=4326;POINT({LATITUDE} {LONGITUDE})')
        # 139 cannot be a latitude, so this row was never in the old order. Swapping would corrupt it.
        already_right = self.add_space('SRID=4326;POINT(139.69 35.68)')

        call_command('migrate', 'theme', self.AFTER_SWAP, verbosity=0)
        old_order.refresh_from_db()
        already_right.refresh_from_db()
        self.assertEqual((old_order.location.x, old_order.location.y), (LONGITUDE, LATITUDE))
        self.assertEqual((already_right.location.x, already_right.location.y), (139.69, 35.68))

        call_command('migrate', 'theme', '0021', verbosity=0)
        old_order.refresh_from_db()
        already_right.refresh_from_db()
        self.assertEqual((old_order.location.x, old_order.location.y), (LATITUDE, LONGITUDE))
        self.assertEqual((already_right.location.x, already_right.location.y), (139.69, 35.68))
