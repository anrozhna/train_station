from rest_framework import viewsets

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
    queryset = Route.objects.all().prefetch_related("source", "destination")
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all().prefetch_related("train_type")
    serializer_class = TrainSerializer

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
    queryset = Journey.objects.all().prefetch_related("route", "train", "crew")
    serializer_class = JourneySerializer

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
        return queryset.distinct()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
