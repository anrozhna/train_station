from django.db import transaction
from rest_framework import serializers

from rail.models import (
    Crew,
    Station,
    Route,
    TrainType,
    Train,
    Journey,
    Order,
    Ticket,
)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
    destination = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
        )


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )


class TrainRetrieveSerializer(TrainSerializer):
    train_type = TrainTypeSerializer(read_only=True)


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
        )


class JourneyListSerializer(serializers.ModelSerializer):
    route = serializers.SlugRelatedField(
        slug_field="route_info",
        read_only=True,
    )
    train = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True,
    )
    crew = serializers.SlugRelatedField(
        slug_field="full_name",
        read_only=True,
        many=True,
    )
    departure_time = serializers.DateTimeField(
        format="%m.%d.%Y %I:%M:%S",
    )
    arrival_time = serializers.DateTimeField(
        format="%m.%d.%Y %I:%M:%S",
    )
    num_seats = serializers.IntegerField(read_only=True)

    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "num_seats",
            "tickets_available",
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "carriage",
            "seat",
        )


class JourneyRetrieveSerializer(JourneyListSerializer):
    route = RouteListSerializer(read_only=True)
    train = TrainListSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_seats = TicketSerializer(many=True, read_only=True, source="tickets")

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "taken_seats",
        )


class TicketListSerializer(serializers.ModelSerializer):
    journey = serializers.SlugRelatedField(
        slug_field="journey_info",
        read_only=True,
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "carriage",
            "seat",
            "journey",
        )


class TicketRetrieveSerializer(TicketListSerializer):
    journey = JourneyListSerializer(read_only=True)

    def validate(self, attrs):
        data = super(TicketListSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["carriage"],
            attrs["seat"],
            attrs["journey"].train,
            serializers.ValidationError
        )
        return data


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        read_only=False,
        allow_empty=False,
    )

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class OrderRetrieveSerializer(OrderSerializer):
    tickets = TicketRetrieveSerializer(many=True, read_only=True)
