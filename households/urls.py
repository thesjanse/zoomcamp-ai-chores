from django.urls import path

from households import views

urlpatterns = [
    path("onboarding/", views.onboarding, name="onboarding"),
    path("households/members/", views.household_members, name="household_members"),
    path(
        "households/members/<int:pk>/promote/",
        views.member_promote,
        name="member_promote",
    ),
    path(
        "households/members/<int:pk>/demote/",
        views.member_demote,
        name="member_demote",
    ),
    path("households/settings/", views.household_settings, name="household_settings"),
]
