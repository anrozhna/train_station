from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from rail.models import  Station
from rail.serializers import StationSerializer

STATION_URL = reverse("rail:station-list")


class UnauthenticatedStationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(STATION_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedStationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

        self.station = Station.objects.create(
            name="Kyiv-Pasazhyrskyi",
            latitude=50.4454,
            longitude=30.4880
        )

    def test_auth_required(self):
        response = self.client.get(STATION_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_station_list(self):
        response = self.client.get(STATION_URL)
        stations = Station.objects.all()
        serializer = StationSerializer(stations, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 1)

    def test_station_retrieve(self):
        url = reverse("rail:station-detail", args=[self.station.id])
        serializer = StationSerializer(self.station)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class AdminStationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(self.admin)

    def test_station_creation(self):
        data = {
            "name": "Lviv",
            "latitude": "49.8397",
            "longitude": "24.0297"
        }

        response = self.client.post(STATION_URL, data)

        station = Station.objects.get(id=response.data["id"])
        serializer = StationSerializer(station)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)
