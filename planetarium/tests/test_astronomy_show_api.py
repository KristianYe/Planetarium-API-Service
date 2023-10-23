from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import AstronomyShow, ShowTheme, PlanetariumDome, ShowSession
from planetarium.serializers import AstronomyShowListSerializer, AstronomyShowDetailSerializer

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")


def sample_astronomy_show(**params):
    defaults = {
        "title": "Sample astronomy show",
        "description": "Sample description",
    }
    defaults.update(params)

    return AstronomyShow.objects.create(**defaults)


def sample_show_theme(**params):
    defaults = {
        "name": "Sample show theme",
    }
    defaults.update(params)

    return ShowTheme.objects.create(**defaults)


def sample_planetarium_dome(**params):
    defaults = {
        "name": "sample dome",
        "rows": 10,
        "seats_in_row": 15
    }
    defaults.update(params)

    return PlanetariumDome.objects.create(**defaults)


def sample_show_session(**params):
    planetarium_dome = sample_planetarium_dome()
    defaults = {
        "show_time": "2022-06-02 14:00:00",
        "astronomy_show": None,
        "planetarium_dome": planetarium_dome,
    }
    defaults.update(params)

    return ShowSession.objects.create(**defaults)


def detail_url(show_id):
    return reverse("planetarium:astronomyshow-detail", args=[show_id])


class UnauthenticatedAstronomyViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAstronomyViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.astronomy_show = sample_astronomy_show()
        self.test_astronomy_show = sample_astronomy_show(title="test")
        self.one_more_astronomy_show = sample_astronomy_show(title="one_more_test")
        self.show_theme = sample_show_theme()
        self.planetarium_dome = sample_planetarium_dome()
        self.show_session = sample_show_session(astronomy_show=self.astronomy_show)

    def test_list_shows(self):
        res = self.client.get(ASTRONOMY_SHOW_URL)

        shows = AstronomyShow.objects.all()
        serializer = AstronomyShowListSerializer(shows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_shows_by_title(self):
        res = self.client.get(ASTRONOMY_SHOW_URL, {"title": "test"})

        shows_with_test_titles = AstronomyShow.objects.filter(title__icontains="test")

        serializer_title = AstronomyShowListSerializer(
            shows_with_test_titles, many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer_title.data)

    def test_filter_show_by_themes(self):
        self.test_astronomy_show.show_themes.add(self.show_theme)

        res = self.client.get(ASTRONOMY_SHOW_URL, {"show_themes": str(self.show_theme.id)})

        test_serializer = AstronomyShowListSerializer(self.test_astronomy_show)
        one_more_test_serializer = AstronomyShowListSerializer(
            self.one_more_astronomy_show
        )
        serializer = AstronomyShowListSerializer(self.astronomy_show)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(test_serializer.data, res.data["results"])
        self.assertNotIn(one_more_test_serializer.data, res.data["results"])
        self.assertNotIn(serializer.data, res.data["results"])

    def test_retrieve_show(self):
        res = self.client.get(detail_url(self.astronomy_show.id))

        serializer = AstronomyShowDetailSerializer(self.astronomy_show)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_show_forbidden(self):
        payload = {
            "title": "test",
            "description": "test",
            "show_themes": [self.show_theme],
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAstronomyShowViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.show_theme = sample_show_theme()

    def test_create_show(self):
        payload = {
            "title": "test",
            "description": "test",
            "show_themes": [self.show_theme.id],
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        show = AstronomyShow.objects.get(id=res.data["id"])

        show_themes = show.show_themes.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            if key not in ("show_themes"):
                self.assertEqual(payload[key], getattr(show, key))

        self.assertEqual(show_themes.count(), 1)
        self.assertIn(self.show_theme, show_themes)

    def test_delete_show(self):
        show = sample_astronomy_show()

        res = self.client.delete(detail_url(show.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
