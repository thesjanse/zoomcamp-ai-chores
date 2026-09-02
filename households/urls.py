from django.urls import path

from households import views

urlpatterns = [
    path("onboarding/", views.onboarding, name="onboarding"),
]
