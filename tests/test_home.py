from django.test import Client


def test_home_returns_200():
    response = Client().get("/")
    assert response.status_code == 200
