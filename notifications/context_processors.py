from notifications.models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications": [], "unread_count": 0}
    unread = (
        Notification.objects.filter(recipient=request.user, is_read=False)
        .order_by("-created_at")[:5]
    )
    return {
        "unread_notifications": unread,
        "unread_count": unread.count(),
    }
