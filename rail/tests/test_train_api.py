import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from rail.models import TrainType, Train
from rail.serializers import (
    TrainSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
)

TRAIN_URL = reverse("rail:train-list")

def image_upload_url(train_id):
    """Return URL for train image upload"""
    return reverse("rail:train-upload-image", args=[train_id])


class UnauthenticatedTrainTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(TRAIN_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

        self.train_type = TrainType.objects.create(name="Passenger")

        self.train = Train.objects.create(
            name="Intercity+ 743",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.train_type,
            image=None
        )

    def test_auth_required(self):
        response = self.client.get(TRAIN_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_train_list(self):
        response = self.client.get(TRAIN_URL)
        trains = Train.objects.all()
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_train_retrieve(self):
        url = reverse("rail:train-detail", args=[self.train.id])
        serializer = TrainRetrieveSerializer(self.train)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="test@test.com", password="test_password"
        )
        self.client.force_authenticate(user=self.user)

        self.train_type = TrainType.objects.create(name="Passenger")

        self.train = Train.objects.create(
            name="Intercity+ 743",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.train_type,
            image=None
        )

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to movie"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        response = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list(self):
        url = TRAIN_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                url,
                {
                    "name": "Test",
                    "cargo_num": 15,
                    "places_in_cargo": 40,
                    "train_type": self.train_type.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Test")
        self.assertTrue(train.image)

    def test_image_url_is_shown_on_train_detail(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(
            reverse("rail:train-detail", args=[self.train.id])
        )

        self.assertIn("image", response.data)

    def test_image_url_is_shown_on_train_list(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_URL)

        self.assertIn("image", res.data[0].keys())


class AdminTrainTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(user=self.admin)

        self.train_type = TrainType.objects.create(name="Passenger")


    def test_train_creation(self):
        data = {
            "name": "Intercity+ 743",
            "cargo_num": 10,
            "places_in_cargo": 50,
            "train_type": self.train_type.id,
            "image": ""
        }
        response = self.client.post(TRAIN_URL, data)

        train = Train.objects.get(id=response.data["id"])
        serializer = TrainSerializer(train)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)
