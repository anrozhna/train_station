from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from rail.models import Station, Route, TrainType, Train, Crew, Journey
from rail.serializers import JourneyListSerializer, JourneyRetrieveSerializer, JourneySerializer

JOURNEY_URL = reverse("rail:journey-list")


class UnauthenticatedJourneyAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(JOURNEY_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedJourneyAPITests(TestCase):
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

        self.train_type = TrainType.objects.create(name="Passenger")

        self.train = Train.objects.create(
            name="Intercity+ 743",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.train_type,
            image=None
        )

        self.crew1 = Crew.objects.create(first_name="John", last_name="Doe")
        self.crew2 = Crew.objects.create(first_name="Jane", last_name="Smith")

        self.journey = Journey.objects.create(
            route=self.route,
            train=self.train,
            departure_time="2025-01-02 12:00:00",
            arrival_time="2025-01-03 12:00:00"
        )

        self.journey.crew.add(self.crew1, self.crew2)

    def test_auth_required(self):
        response = self.client.get(JOURNEY_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_journey_list(self):
        response = self.client.get(JOURNEY_URL)
        journeys = Journey.objects.all()
        serializer = JourneyListSerializer(journeys, many=True)

        for journey in response.data:
            self.assertIn("tickets_available", journey)
            self.assertIn("num_seats", journey)

        for journey in response.data:
            journey.pop("tickets_available", None)
            journey.pop("num_seats", None)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_journey_retrieve(self):
        url = reverse("rail:journey-detail", args=[self.journey.id])
        serializer = JourneyRetrieveSerializer(self.journey)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_journey_filter_by_train_id(self):
        response = self.client.get(
            JOURNEY_URL,
            {
                "train_id": "1",
            }
        )
        journeys = Journey.objects.filter(
            train__id="1"
        )
        serializer = JourneyListSerializer(journeys, many=True)

        for journey in response.data:
            journey.pop("tickets_available", None)
            journey.pop("num_seats", None)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class AdminJourneyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(user=self.admin)

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

        self.train_type = TrainType.objects.create(name="Passenger")

        self.train = Train.objects.create(
            name="Intercity+ 743",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.train_type,
            image=None
        )

        self.crew1 = Crew.objects.create(first_name="John", last_name="Doe")
        self.crew2 = Crew.objects.create(first_name="Jane", last_name="Smith")

    def test_journey_creation(self):
        data = {
            "route": self.route.id,
            "train": self.train.id,
            "departure_time": "2025-01-02 15:00:00",
            "arrival_time": "2025-01-03 15:00:00",
            "crew": [self.crew1.id, self.crew2.id]
        }
        response = self.client.post(JOURNEY_URL, data)

        journey = Journey.objects.get(id=response.data["id"])
        serializer = JourneySerializer(journey)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)
