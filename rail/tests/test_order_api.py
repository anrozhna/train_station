from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from rail.models import Order
from rail.serializers import OrderListSerializer


ORDER_URL = reverse("rail:order-list")


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ORDER_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            user=self.user
        )

    def test_auth_required(self):
        response = self.client.get(ORDER_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_orders_list(self):
        response = self.client.get(ORDER_URL)
        orders = Order.objects.all()
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_order_retrieve(self):
        url = reverse("rail:order-detail", args=[self.order.id])
        serializer = OrderListSerializer(self.order)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_orders_filter_by_created_time(self):
        today = now().date()

        response = self.client.get(
            ORDER_URL,
            {
                "created_at": today.isoformat(),
            }
        )

        orders = Order.objects.filter(
            created_at__date=today
        )
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)


class AdminOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(self.admin)


    def test_cannot_access_other_users_orders(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="password123"
        )
        other_user_order = Order.objects.create(user=other_user)

        url = reverse("rail:order-detail", args=[other_user_order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
