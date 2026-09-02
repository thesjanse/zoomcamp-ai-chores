from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.models import Chore
from notifications.models import Notification


class Command(BaseCommand):
    help = "Create notifications for overdue assigned chores."

    def handle(self, *args, **options):
        today = timezone.localdate()
        chore_ids = []
        overdue = Chore.objects.filter(
            due_date__lt=today,
            assigned_to__isnull=False,
            due_date__isnull=False,
        ).exclude(status="done")
        for chore in overdue:
            Notification.objects.get_or_create(
                recipient=chore.assigned_to,
                chore=chore,
                defaults={
                    "title": f"Overdue: {chore.title}",
                    "body": "This chore is overdue.",
                },
            )
            chore_ids.append(chore.pk)
        self.stdout.write(
            self.style.SUCCESS(
                f"Notified {len(chore_ids)} overdue chore(s)."
            )
        )
