from django.db.models import F, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from rail.models import (
    Crew,
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Order,
)
from rail.serializers import (
    CrewSerializer,
    StationSerializer,
    RouteSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    JourneySerializer,
    OrderSerializer,
    RouteListSerializer,
    TrainListSerializer,
    JourneyListSerializer,
    TrainRetrieveSerializer,
    JourneyRetrieveSerializer,
    OrderRetrieveSerializer, OrderListSerializer, TrainImageSerializer,
)


def _params_to_ints(query_string):
    """Converts a list of string IDs to a list of integers"""
    return [int(str_id) for str_id in query_string.split(",")]


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all().prefetch_related("journeys")
    serializer_class = CrewSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all().prefetch_related("train_type")

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainRetrieveSerializer
        if self.action == "upload_image":
            return TrainImageSerializer
        return TrainSerializer

    def get_queryset(self):
        queryset = self.queryset
        train_types = self.request.query_params.get("train-types", None)

        if train_types:
            train_types = _params_to_ints(train_types)
            queryset = queryset.filter(train_type__id__in=train_types)

        return queryset.distinct()

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific train."""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "train-types",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by train_type id (ex. ?train-types=2,5)",
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get a list of trains with filtering by train_type id."""
        return super().list(request, *args, **kwargs)


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyRetrieveSerializer
        return JourneySerializer

    def get_queryset(self):
        queryset = self.queryset
        train = self.request.query_params.get("train", None)

        if train:
            train = _params_to_ints(train)
            queryset = queryset.filter(train__id__in=train)

        if self.action == "list":
            queryset = (
                queryset.select_related(
                    "route__source",
                    "route__destination",
                    "train",
                ).prefetch_related("crew")
                .annotate(
                    num_seats=F("train__cargo_num") * F("train__places_in_cargo"),
                    tickets_available=F("num_seats") - Count("tickets"),
                )
            )

        if self.action == "retrieve":
            queryset = (
                queryset.select_related(
                    "route__source",
                    "route__destination",
                    "train__train_type",
                ).prefetch_related("crew")
            )

        return queryset.distinct().order_by("id")


class OrderSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"
    max_page_size = 20


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderRetrieveSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets__journey__route",
                "tickets__journey__train",
                "tickets__journey__crew"
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
