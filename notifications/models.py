from django.conf import settings
from django.db import models


class Notification(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    chore = models.ForeignKey(
        "chores.Chore",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("recipient", "chore")

    def __str__(self):
        return self.title
