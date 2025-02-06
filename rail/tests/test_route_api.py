from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from rail.models import  Station, Route
from rail.serializers import RouteSerializer, RouteListSerializer

ROUTE_URL = reverse("rail:route-list")


class UnauthenticatedRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ROUTE_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

        self.source_station = Station.objects.create(
            name="Kyiv-Pasazhyrskyi",
            latitude=50.4454,
            longitude=30.4880
        )

        self.destination_station = Station.objects.create(
            name="Lviv",
            latitude=49.8397,
            longitude=24.0297
        )

        self.route = Route.objects.create(
            source=self.source_station,
            destination=self.destination_station,
            distance=540
        )

    def test_auth_required(self):
        response = self.client.get(ROUTE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_route_list(self):
        response = self.client.get(ROUTE_URL)
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 1)

    def test_route_retrieve(self):
        url = reverse("rail:route-detail", args=[self.route.id])
        serializer = RouteSerializer(self.route)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class AdminRouteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(self.admin)

        self.source_station = Station.objects.create(
            name="Kyiv-Pasazhyrskyi",
            latitude=50.4454,
            longitude=30.4880
        )

        self.destination_station = Station.objects.create(
            name="Lviv",
            latitude=49.8397,
            longitude=24.0297
        )

    def test_route_creation(self):
        data = {
            "source": self.source_station.id,
            "destination": self.destination_station.id,
            "distance": "540"
        }

        response = self.client.post(ROUTE_URL, data)

        route = Route.objects.get(id=response.data["id"])
        serializer = RouteSerializer(route)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)
