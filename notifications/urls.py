from django.urls import path

from notifications import views

urlpatterns = [
    path(
        "notifications/<int:pk>/read/",
        views.notification_read,
        name="notification_read",
    ),
    path(
        "notifications/read-all/",
        views.notification_read_all,
        name="notification_read_all",
    ),
]
