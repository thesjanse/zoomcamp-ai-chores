from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from notifications.models import Notification


@login_required
def notification_read(request, pk):
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    return HttpResponse(status=200)


@login_required
def notification_read_all(request):
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    return HttpResponse(status=200)
