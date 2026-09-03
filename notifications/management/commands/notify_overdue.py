from collections import defaultdict

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from chores.models import Chore
from notifications.models import Notification


class Command(BaseCommand):
    help = "Create notifications for overdue assigned chores."

    def handle(self, *args, **options):
        today = timezone.localdate()
        chore_ids = []
        new_by_user = defaultdict(list)
        overdue = Chore.objects.filter(
            due_date__lt=today,
            assigned_to__isnull=False,
            due_date__isnull=False,
        ).exclude(status="done")
        for chore in overdue:
            _, created = Notification.objects.get_or_create(
                recipient=chore.assigned_to,
                chore=chore,
                defaults={
                    "title": f"Overdue: {chore.title}",
                    "body": "This chore is overdue.",
                },
            )
            chore_ids.append(chore.pk)
            if created:
                new_by_user[chore.assigned_to].append(chore)
        for recipient, chores in new_by_user.items():
            if not recipient.email or not recipient.is_active:
                continue
            count = len(chores)
            subject = f"You have {count} overdue chore(s)"
            body = render_to_string(
                "notifications/overdue_digest.txt",
                {"chores": chores, "count": count},
            )
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                )
            except Exception as exc:
                self.stderr.write(
                    f"Failed to send email to {recipient.email}: {exc}"
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Notified {len(chore_ids)} overdue chore(s)."
            )
        )
