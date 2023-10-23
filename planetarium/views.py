from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation,
)
from planetarium.permissions import IsAdminOrIfAuthenticatedReadOnly
from planetarium.serializers import (
    ShowThemeSerializer,
    AstronomyShowSerializer,
    PlanetariumDomeSerializer,
    ShowSessionSerializer,
    ReservationSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
    ShowSessionListSerializer,
    ShowSessionDetailSerializer,
    ReservationListSerializer,
)


class PageFivePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50


class PageTenPagination(PageFivePagination):
    page_size = 10


class ShowThemeViewSet(viewsets.ModelViewSet):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializer
    pagination_class = PageTenPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly, )

    def get_queryset(self):
        queryset = self.queryset

        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class AstronomyShowViewSet(viewsets.ModelViewSet):
    queryset = AstronomyShow.objects.all()
    serializer_class = AstronomyShowSerializer
    pagination_class = PageFivePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly, )

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("show_theme")

        title = self.request.query_params.get("title")
        show_theme_name = self.request.query_params.get("show_theme_name")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if show_theme_name:
            queryset = queryset.filter(
                show_theme__name__icontains=show_theme_name
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer

        if self.action == "retrieve":
            return AstronomyShowDetailSerializer

        return self.serializer_class


class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer
    pagination_class = PageTenPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly, )

    def get_queryset(self):
        queryset = self.queryset

        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = ShowSession.objects.all()
    serializer_class = ShowSessionSerializer
    pagination_class = PageFivePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly, )


    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer

        if self.action == "retrieve":
            return ShowSessionDetailSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset.select_related(
            "astronomy_show", "planetarium_dome"
        )

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("planetarium_dome__seats_in_row")
                    * F("planetarium_dome__rows")
                    - Count("tickets")
                )
            )

        date = self.request.query_params.get("date")
        show_title = self.request.query_params.get("show_title")

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if show_title:
            queryset = queryset.filter(astronomy_show__title__icontains=show_title)

        return queryset.distinct()


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    pagination_class = PageFivePagination
    permission_classes = (IsAuthenticated, )


    def get_queryset(self):
        queryset = self.queryset.prefetch_related(
            "tickets__show_session__astronomy_show",
            "tickets__show_session__planetarium_dome",
        )

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
