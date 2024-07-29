from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

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
    OrderRetrieveSerializer, OrderListSerializer,
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
        return TrainSerializer

    def get_queryset(self):
        queryset = self.queryset
        train_types = self.request.query_params.get("train_types", None)

        if train_types:
            train_types = _params_to_ints(train_types)
            queryset = queryset.filter(train_type__id__in=train_types)

        return queryset.distinct()


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
