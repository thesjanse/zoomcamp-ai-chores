from households.models import HouseholdMember
from notifications.models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications": [],
            "unread_count": 0,
            "has_household": False,
            "is_admin": False,
        }
    membership = HouseholdMember.objects.filter(user=request.user).first()
    unread = (
        Notification.objects.filter(recipient=request.user, is_read=False)
        .order_by("-created_at")[:5]
    )
    return {
        "unread_notifications": unread,
        "unread_count": unread.count(),
        "has_household": membership is not None,
        "is_admin": membership.is_admin if membership else False,
    }
