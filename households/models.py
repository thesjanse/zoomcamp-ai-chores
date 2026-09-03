import secrets
import string

from django.core.exceptions import ValidationError
from django.db import models


class Household(models.Model):
    name = models.CharField(max_length=255)
    invite_code = models.CharField(
        max_length=12, unique=True, blank=True, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank."})

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_invite_code():
        alphabet = string.ascii_uppercase + string.digits
        code = "HOME-" + "".join(secrets.choice(alphabet) for _ in range(4))
        while Household.objects.filter(invite_code=code).exists():
            code = "HOME-" + "".join(secrets.choice(alphabet) for _ in range(4))
        return code


class HouseholdMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "admin"
        MEMBER = "member", "member"

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="household_memberships"
    )
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("household", "user")

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.user} in {self.household}"
