from datetime import date
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from chores.models import Chore
from households.models import Household, HouseholdMember
from notifications.models import Notification


class NotifyOverdueCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)

        self.today = date(2026, 9, 15)
        self.overdue = date(2026, 9, 10)

    def test_creates_exactly_one_notification_for_overdue_assigned(self):
        chore = Chore.objects.create(
            title="Take out the trash",
            household=self.household,
            assigned_to=self.user,
            status="in_progress",
            due_date=self.overdue,
        )
        with mock.patch(
            "django.utils.timezone.localdate", return_value=self.today
        ):
            call_command("notify_overdue")
        notifications = Notification.objects.all()
        self.assertEqual(notifications.count(), 1)
        notification = notifications[0]
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.chore, chore)
        self.assertEqual(notification.title, "Overdue: Take out the trash")
        self.assertFalse(notification.is_read)

    def test_running_twice_is_idempotent(self):
        Chore.objects.create(
            title="Trash",
            household=self.household,
            assigned_to=self.user,
            due_date=self.overdue,
        )
        with mock.patch(
            "django.utils.timezone.localdate", return_value=self.today
        ):
            call_command("notify_overdue")
            call_command("notify_overdue")
        self.assertEqual(Notification.objects.count(), 1)

    def test_done_overdue_chore_creates_no_notification(self):
        Chore.objects.create(
            title="Done late",
            household=self.household,
            assigned_to=self.user,
            status="done",
            due_date=self.overdue,
        )
        with mock.patch(
            "django.utils.timezone.localdate", return_value=self.today
        ):
            call_command("notify_overdue")
        self.assertEqual(Notification.objects.count(), 0)

    def test_due_today_creates_no_notification(self):
        Chore.objects.create(
            title="Due today",
            household=self.household,
            assigned_to=self.user,
            due_date=self.today,
        )
        with mock.patch(
            "django.utils.timezone.localdate", return_value=self.today
        ):
            call_command("notify_overdue")
        self.assertEqual(Notification.objects.count(), 0)

    def test_unassigned_chore_creates_no_notification(self):
        Chore.objects.create(
            title="Unassigned",
            household=self.household,
            due_date=self.overdue,
        )
        with mock.patch(
            "django.utils.timezone.localdate", return_value=self.today
        ):
            call_command("notify_overdue")
        self.assertEqual(Notification.objects.count(), 0)


class NotificationHeaderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")

    def test_page_renders_unread_count_and_title(self):
        n = Notification.objects.create(
            recipient=self.user,
            chore=None,
            title="Overdue: Trash",
            body="This chore is overdue.",
        )
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notifications (1)")
        self.assertContains(response, "Overdue: Trash")

    def test_read_notification_not_shown_as_unread(self):
        Notification.objects.create(
            recipient=self.user,
            chore=None,
            title="Read me",
            is_read=True,
        )
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notifications (0)")
        self.assertNotContains(response, "Read me")

    def test_anonymous_page_handles_context_processor(self):
        self.client.logout()
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)


class NotificationReadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")

    def test_mark_read_sets_is_read_and_returns_200_idempotent(self):
        n = Notification.objects.create(
            recipient=self.user, chore=None, title="Msg"
        )
        response = self.client.post(reverse("notification_read", args=[n.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        second = self.client.post(
            reverse("notification_read", args=[n.pk])
        )
        self.assertEqual(second.status_code, 200)

    def test_foreign_notification_404_and_not_mutated(self):
        n = Notification.objects.create(
            recipient=self.other_user, chore=None, title="Other"
        )
        response = self.client.post(reverse("notification_read", args=[n.pk]))
        self.assertEqual(response.status_code, 404)
        n.refresh_from_db()
        self.assertFalse(n.is_read)

    def test_anonymous_read_redirects_to_login(self):
        self.client.logout()
        n = Notification.objects.create(
            recipient=self.user, chore=None, title="Msg"
        )
        response = self.client.post(reverse("notification_read", args=[n.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_anonymous_read_all_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(reverse("notification_read_all"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_read_all_marks_all_read_and_returns_200(self):
        for i in range(3):
            Notification.objects.create(
                recipient=self.user, chore=None, title=f"Msg {i}"
            )
        response = self.client.post(reverse("notification_read_all"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user, is_read=False
            ).count(),
            0,
        )
