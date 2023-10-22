from rest_framework import serializers

from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation,
    Ticket,
)


class ShowThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTheme
        fields = "__all__"


class AstronomyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = "__all__"


class AstronomyShowListSerializer(AstronomyShowSerializer):
    show_theme = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )


class AstronomyShowDetailSerializer(AstronomyShowSerializer):
    show_theme = ShowThemeSerializer(many=True, read_only=True)


class PlanetariumDomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanetariumDome
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class ShowSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowSession
        fields = "__all__"


class ShowSessionListSerializer(serializers.ModelSerializer):
    astronomy_show_title = serializers.CharField(
        source="astronomy_show.title", read_only=True
    )
    planetarium_dome_name = serializers.CharField(
        source="planetarium_dome.name", read_only=True
    )
    planetarium_dome_capacity = serializers.IntegerField(
        source="planetarium_dome.capacity", read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "show_time",
            "astronomy_show_title",
            "planetarium_dome_name",
            "planetarium_dome_capacity",
            "tickets_available",
        )


class ShowSessionTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class ShowSessionDetailSerializer(serializers.ModelSerializer):
    astronomy_show = AstronomyShowListSerializer(many=False, read_only=True)
    planetarium_dome = PlanetariumDomeSerializer(many=False, read_only=True)
    taken_places = ShowSessionTicketSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "show_time",
            "astronomy_show",
            "planetarium_dome",
            "taken_places",
        )


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"
