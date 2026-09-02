from datetime import timedelta

from django.utils import timezone


def chore_color_class(chore, today=None):
    if today is None:
        today = timezone.localdate()
    if chore.due_date is None:
        return "calendar-none"
    if chore.status == "done":
        return "calendar-on-time"
    if chore.due_date < today:
        return "calendar-overdue"
    if chore.due_date <= today + timedelta(days=3):
        return "calendar-due-soon"
    return "calendar-on-time"