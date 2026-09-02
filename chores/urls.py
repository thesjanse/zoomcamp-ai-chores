from django.urls import path

from chores import views

urlpatterns = [
    path("chores/", views.chore_list, name="chore_list"),
    path("chores/new/", views.chore_create, name="chore_create"),
    path("chores/<int:pk>/", views.chore_detail, name="chore_detail"),
    path("chores/<int:pk>/edit/", views.chore_update, name="chore_update"),
    path("chores/<int:pk>/delete/", views.chore_delete, name="chore_delete"),
]
