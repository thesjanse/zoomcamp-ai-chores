from datetime import date, timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from chores.models import Chore
from chores.utils import chore_color_class
from households.models import Household, HouseholdMember


def count_class(response, css_class):
    return response.content.decode().count(f'class="{css_class}"')


class ChoreModelTest(TestCase):
    def setUp(self):
        self.household = Household.objects.create(name="The Smiths")

    def test_create_persists_and_defaults_open_unassigned(self):
        chore = Chore.objects.create(
            title="Take out the trash", household=self.household
        )
        self.assertEqual(Chore.objects.count(), 1)
        chore.refresh_from_db()
        self.assertEqual(chore.title, "Take out the trash")
        self.assertEqual(chore.status, "open")
        self.assertIsNone(chore.assigned_to)
        self.assertIsNotNone(chore.created_at)

    def test_status_choices(self):
        self.assertCountEqual(
            [c[0] for c in Chore.Status.choices],
            ["open", "in_progress", "done"],
        )

    def test_read_back_field_values(self):
        user = User.objects.create_user("worker")
        chore = Chore.objects.create(
            title="Dishes",
            description="Wash and dry",
            assigned_to=user,
            due_date="2026-12-01",
            status="in_progress",
            household=self.household,
        )
        chore.refresh_from_db()
        self.assertEqual(chore.description, "Wash and dry")
        self.assertEqual(chore.assigned_to, user)
        self.assertEqual(str(chore.due_date), "2026-12-01")
        self.assertEqual(chore.status, "in_progress")
        self.assertEqual(chore.household, self.household)

    def test_optional_description_and_due_date(self):
        chore = Chore.objects.create(
            title="No details", household=self.household
        )
        self.assertIsNone(chore.description)
        self.assertIsNone(chore.due_date)


class ChoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household
        )

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_user_without_household_redirected_to_onboarding(self):
        no_house_user = User.objects.create_user("homeless")
        self.client.force_login(no_house_user)
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding"))

    def test_list_shows_only_current_users_household_chores(self):
        mine = Chore.objects.create(
            title="My chore", household=self.household
        )
        foreign = Chore.objects.create(
            title="Their chore", household=self.other_household
        )
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, mine.title)
        self.assertNotContains(response, foreign.title)

    def test_create_persists_and_redirects_to_list(self):
        response = self.client.post(reverse("chore_create"), {
            "title": "Mow the lawn",
            "description": "Front and back",
            "due_date": "2026-12-15",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("chore_list"))
        chore = Chore.objects.get(title="Mow the lawn")
        self.assertEqual(chore.household, self.household)
        self.assertEqual(chore.description, "Front and back")
        self.assertEqual(str(chore.due_date), "2026-12-15")
        self.assertEqual(chore.status, "open")
        self.assertIsNone(chore.assigned_to)

    def test_create_with_empty_description_and_no_due_date(self):
        response = self.client.post(reverse("chore_create"), {
            "title": "Sweep floor",
        })
        self.assertEqual(response.status_code, 302)
        chore = Chore.objects.get(title="Sweep floor")
        self.assertEqual(chore.description, "")
        self.assertIsNone(chore.due_date)

    def test_create_get_renders_form(self):
        response = self.client.get(reverse("chore_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "title")
        self.assertContains(response, "description")
        self.assertContains(response, "due_date")
        self.assertNotContains(response, "assigned_to")
        self.assertNotContains(response, "status")

    def test_detail_shows_chore(self):
        chore = Chore.objects.create(
            title="Clean bathroom", household=self.household
        )
        response = self.client.get(reverse("chore_detail", args=[chore.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, chore.title)

    def test_update_edits_and_redirects_to_list(self):
        chore = Chore.objects.create(
            title="Old title", household=self.household
        )
        response = self.client.post(
            reverse("chore_update", args=[chore.pk]),
            {"title": "New title", "description": "", "due_date": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("chore_list"))
        chore.refresh_from_db()
        self.assertEqual(chore.title, "New title")

    def test_delete_get_does_not_delete(self):
        chore = Chore.objects.create(
            title="Do not delete yet", household=self.household
        )
        response = self.client.get(reverse("chore_delete", args=[chore.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, chore.title)
        self.assertTrue(Chore.objects.filter(pk=chore.pk).exists())

    def test_delete_post_deletes_and_redirects_to_list(self):
        chore = Chore.objects.create(
            title="Delete me", household=self.household
        )
        response = self.client.post(reverse("chore_delete", args=[chore.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("chore_list"))
        self.assertFalse(Chore.objects.filter(pk=chore.pk).exists())

    def test_update_does_not_change_status_via_form(self):
        chore = Chore.objects.create(
            title="Stable status", household=self.household, status="done"
        )
        response = self.client.post(
            reverse("chore_update", args=[chore.pk]),
            {"title": "Stable status", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        chore.refresh_from_db()
        self.assertEqual(chore.status, "done")

    def test_foreign_chore_detail_404(self):
        foreign = Chore.objects.create(
            title="Secret", household=self.other_household
        )
        response = self.client.get(reverse("chore_detail", args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Chore.objects.filter(pk=foreign.pk).exists())

    def test_foreign_chore_update_404_and_not_modified(self):
        foreign = Chore.objects.create(
            title="Others", household=self.other_household
        )
        response = self.client.post(
            reverse("chore_update", args=[foreign.pk]),
            {"title": "Hacked"},
        )
        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.title, "Others")

    def test_foreign_chore_delete_404_and_not_deleted(self):
        foreign = Chore.objects.create(
            title="Keep me", household=self.other_household
        )
        response = self.client.post(reverse("chore_delete", args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Chore.objects.filter(pk=foreign.pk).exists())


class ChoreMarketTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household
        )

    def test_market_lists_only_open_unassigned_chores(self):
        open_chore = Chore.objects.create(
            title="Open one", household=self.household
        )
        assigned = Chore.objects.create(
            title="Assigned", household=self.household,
            assigned_to=self.user, status="in_progress",
        )
        done = Chore.objects.create(
            title="Done", household=self.household, status="done"
        )
        foreign = Chore.objects.create(
            title="Foreign", household=self.other_household
        )
        response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, open_chore.title)
        self.assertNotContains(response, assigned.title)
        self.assertNotContains(response, done.title)
        self.assertNotContains(response, foreign.title)

    def test_market_empty_state(self):
        response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chores available to claim.")

    def test_claim_assigns_and_sets_in_progress_returns_200(self):
        chore = Chore.objects.create(
            title="Claim me", household=self.household
        )
        response = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        chore.refresh_from_db()
        self.assertEqual(chore.assigned_to, self.user)
        self.assertEqual(chore.status, "in_progress")

    def test_claim_removes_chore_from_market(self):
        chore = Chore.objects.create(
            title="Gone", household=self.household
        )
        self.client.post(reverse("chore_claim", args=[chore.pk]))
        market = self.client.get(reverse("chore_market"))
        self.assertNotContains(market, chore.title)

    def test_double_claim_preserves_original_assignee(self):
        chore = Chore.objects.create(
            title="One shot", household=self.household
        )
        first = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(first.status_code, 200)
        second = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(second.status_code, 200)
        chore.refresh_from_db()
        self.assertEqual(chore.assigned_to, self.user)
        self.assertEqual(chore.status, "in_progress")

        other_member = User.objects.create_user("other_member")
        HouseholdMember.objects.create(
            user=other_member, household=self.household
        )
        self.client.force_login(other_member)
        third = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(third.status_code, 200)
        chore.refresh_from_db()
        self.assertEqual(chore.assigned_to, self.user)
        self.assertEqual(chore.status, "in_progress")

    def test_foreign_user_claims_404_and_not_modified(self):
        chore = Chore.objects.create(
            title="Mine", household=self.household
        )
        self.client.force_login(self.other_user)
        response = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(response.status_code, 404)
        chore.refresh_from_db()
        self.assertIsNone(chore.assigned_to)
        self.assertEqual(chore.status, "open")

    def test_foreign_user_market_404(self):
        self.client.force_login(self.other_user)
        Chore.objects.create(title="Mine", household=self.household)
        response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Mine")

    def test_anonymous_claim_redirected_to_login(self):
        self.client.logout()
        chore = Chore.objects.create(
            title="Anon", household=self.household
        )
        response = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_anonymous_market_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_no_household_user_redirected_to_onboarding_market(self):
        no_house_user = User.objects.create_user("homeless")
        self.client.force_login(no_house_user)
        response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding"))

    def test_no_household_user_redirected_to_onboarding_claim(self):
        no_house_user = User.objects.create_user("homeless2")
        chore = Chore.objects.create(
            title="Any", household=self.household
        )
        self.client.force_login(no_house_user)
        response = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding"))

    def test_claim_form_uses_htmx(self):
        chore = Chore.objects.create(
            title="HTMX chore", household=self.household
        )
        response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "htmx.org@1.9.12")
        self.assertContains(
            response,
            f'hx-post="{reverse("chore_claim", args=[chore.pk])}"',
        )
        self.assertContains(response, "hx-target=\"closest li\"")
        self.assertContains(response, "hx-swap=\"outerHTML\"")


class ChoreListLateIndicatorsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household
        )

    def test_overdue_open_chore_row_renders_overdue_class(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Late", household=self.household,
                status="open", due_date=date(2026, 9, 10),
            )
            response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count_class(response, "calendar-overdue"), 1)

    def test_overdue_in_progress_chore_row_renders_overdue_class(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Late progress", household=self.household,
                status="in_progress", assigned_to=self.user,
                due_date=date(2026, 9, 10),
            )
            response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count_class(response, "calendar-overdue"), 1)

    def test_due_today_chore_row_not_overdue(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Due today", household=self.household,
                status="in_progress", assigned_to=self.user,
                due_date=date(2026, 9, 15),
            )
            response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count_class(response, "calendar-overdue"), 0)

    def test_done_overdue_chore_not_marked_overdue(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Done late", household=self.household,
                status="done", due_date=date(2026, 9, 10),
            )
            response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count_class(response, "calendar-overdue"), 0)

    def test_foreign_household_overdue_chore_does_not_leak_overdue_class(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Foreign", household=self.other_household,
                status="open", due_date=date(2026, 9, 10),
            )
            response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Foreign")
        self.assertEqual(count_class(response, "calendar-overdue"), 0)


class ChoreMarketLateIndicatorsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household
        )

    def test_overdue_open_unassigned_market_row_overdue(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Late market", household=self.household,
                status="open", due_date=date(2026, 9, 10),
            )
            response = self.client.get(reverse("chore_market"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count_class(response, "calendar-overdue"), 1)


class ChoreDoneTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household
        )

    def test_mark_done_sets_status_and_completed_at(self):
        chore = Chore.objects.create(
            title="Finish project",
            household=self.household,
            assigned_to=self.user,
            status="in_progress",
        )
        response = self.client.post(reverse("chore_done", args=[chore.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        chore.refresh_from_db()
        self.assertEqual(chore.status, "done")
        self.assertIsNotNone(chore.completed_at)
        self.assertLess(chore.completed_at - timezone.now(), timedelta(seconds=10))

    def test_mark_done_removes_chore_from_list(self):
        chore = Chore.objects.create(
            title="Disappear me",
            household=self.household,
            assigned_to=self.user,
            status="in_progress",
        )
        self.client.post(reverse("chore_done", args=[chore.pk]))
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, chore.title)

    def test_unclaimed_chore_cannot_be_marked_done(self):
        chore = Chore.objects.create(
            title="Unclaimed", household=self.household
        )
        response = self.client.post(reverse("chore_done", args=[chore.pk]))
        self.assertEqual(response.status_code, 200)
        chore.refresh_from_db()
        self.assertEqual(chore.status, "open")
        self.assertIsNone(chore.assigned_to)

    def test_already_done_chore_not_marked_done_again(self):
        original_completed_at = timezone.now() - timedelta(days=1)
        chore = Chore.objects.create(
            title="Already done",
            household=self.household,
            assigned_to=self.user,
            status="done",
            completed_at=original_completed_at,
        )
        response = self.client.post(reverse("chore_done", args=[chore.pk]))
        self.assertEqual(response.status_code, 200)
        chore.refresh_from_db()
        self.assertEqual(chore.status, "done")
        self.assertEqual(chore.completed_at, original_completed_at)

    def test_foreign_chore_done_404(self):
        chore = Chore.objects.create(
            title="Foreign", household=self.other_household
        )
        response = self.client.post(reverse("chore_done", args=[chore.pk]))
        self.assertEqual(response.status_code, 404)
        chore.refresh_from_db()
        self.assertEqual(chore.status, "open")

    def test_anonymous_done_redirected_to_login(self):
        self.client.logout()
        chore = Chore.objects.create(
            title="Anon", household=self.household
        )
        response = self.client.post(reverse("chore_done", args=[chore.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_no_household_user_done_redirected_to_onboarding(self):
        no_house_user = User.objects.create_user("homeless")
        self.client.force_login(no_house_user)
        chore = Chore.objects.create(
            title="Any", household=self.household
        )
        response = self.client.post(reverse("chore_done", args=[chore.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding"))

    def test_mark_done_button_shown_only_to_assignee_of_in_progress(self):
        assigned = Chore.objects.create(
            title="My task",
            household=self.household,
            assigned_to=self.user,
            status="in_progress",
        )
        response = self.client.get(reverse("chore_detail", args=[assigned.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "htmx.org@1.9.12")
        self.assertContains(
            response,
            f'hx-post="{reverse("chore_done", args=[assigned.pk])}"',
        )
        self.assertContains(response, "hx-target=\"closest form\"")
        self.assertContains(response, "hx-swap=\"outerHTML\"")

    def test_mark_done_button_hidden_for_open_and_done_and_other_assignee(self):
        open_chore = Chore.objects.create(
            title="Open", household=self.household
        )
        response = self.client.get(reverse("chore_detail", args=[open_chore.pk]))
        self.assertNotContains(response, "Mark Done")

        done_chore = Chore.objects.create(
            title="Done", household=self.household, status="done"
        )
        response = self.client.get(reverse("chore_detail", args=[done_chore.pk]))
        self.assertNotContains(response, "Mark Done")

        other = User.objects.create_user("assignee")
        HouseholdMember.objects.create(user=other, household=self.household)
        other_chore = Chore.objects.create(
            title="Theirs",
            household=self.household,
            assigned_to=other,
            status="in_progress",
        )
        response = self.client.get(reverse("chore_detail", args=[other_chore.pk]))
        self.assertNotContains(response, "Mark Done")


class ChoreColorClassTest(TestCase):
    def test_no_due_date_is_none(self):
        chore = Chore(due_date=None, status="open")
        self.assertEqual(chore_color_class(chore, today=timezone.localdate()), "calendar-none")

    def test_done_is_always_on_time(self):
        today = timezone.localdate()
        overdue_done = Chore(due_date=today - timedelta(days=10), status="done")
        soon_done = Chore(due_date=today + timedelta(days=1), status="done")
        self.assertEqual(chore_color_class(overdue_done, today=today), "calendar-on-time")
        self.assertEqual(chore_color_class(soon_done, today=today), "calendar-on-time")

    def test_overdue_open_is_red(self):
        today = timezone.localdate()
        chore = Chore(due_date=today - timedelta(days=1), status="open")
        self.assertEqual(chore_color_class(chore, today=today), "calendar-overdue")

    def test_due_soon_is_yellow(self):
        today = timezone.localdate()
        due_today = Chore(due_date=today, status="in_progress")
        due_in_three = Chore(due_date=today + timedelta(days=3), status="in_progress")
        in_future = Chore(due_date=today + timedelta(days=4), status="open")
        self.assertEqual(chore_color_class(due_today, today=today), "calendar-due-soon")
        self.assertEqual(chore_color_class(due_in_three, today=today), "calendar-due-soon")
        self.assertEqual(chore_color_class(in_future, today=today), "calendar-on-time")


class ChoreCalendarTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        HouseholdMember.objects.create(user=self.user, household=self.household)
        self.client.force_login(self.user)

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household
        )

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("chore_calendar"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_user_without_household_redirected_to_onboarding(self):
        no_house_user = User.objects.create_user("homeless")
        self.client.force_login(no_house_user)
        response = self.client.get(reverse("chore_calendar"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding"))

    def test_renders_month_label_and_grid(self):
        today = timezone.localdate()
        response = self.client.get(reverse("chore_calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, today.strftime("%B %Y"))
        for header in ("<th>Mon</th>", "<th>Sun</th>"):
            self.assertContains(response, header)

    def test_chores_placed_in_correct_due_date_cell(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            day15 = Chore.objects.create(
                title="Due on 15th",
                household=self.household,
                due_date=date(2026, 9, 15),
            )
            day20 = Chore.objects.create(
                title="Due on 20th",
                household=self.household,
                due_date=date(2026, 9, 20),
            )
            response = self.client.get(reverse("chore_calendar"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        day15_cell = html.find("15</div>")
        day20_cell = html.find("20</div>")
        self.assertNotEqual(day15_cell, -1)
        self.assertNotEqual(day20_cell, -1)
        title15 = html.find(day15.title, day15_cell)
        title20 = html.find(day20.title, day20_cell)
        self.assertNotEqual(title15, -1)
        self.assertNotEqual(title20, -1)
        self.assertLess(title15, day20_cell)

    def test_color_coding_renders_classes(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            overdue = Chore.objects.create(
                title="Overdue", household=self.household,
                status="open", due_date=date(2026, 9, 1),
            )
            due_soon = Chore.objects.create(
                title="Due soon", household=self.household,
                status="in_progress", due_date=date(2026, 9, 16),
            )
            on_time = Chore.objects.create(
                title="On time", household=self.household,
                status="open", due_date=date(2026, 9, 25),
            )
            response = self.client.get(reverse("chore_calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, overdue.title)
        self.assertContains(response, due_soon.title)
        self.assertContains(response, on_time.title)
        self.assertEqual(
            count_class(response, "calendar-overdue"), 1
        )
        self.assertEqual(count_class(response, "calendar-due-soon"), 1)
        self.assertEqual(count_class(response, "calendar-on-time"), 1)

    def test_done_overdue_renders_green_not_red(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            done = Chore.objects.create(
                title="Done overdue", household=self.household,
                status="done", due_date=date(2026, 9, 10),
            )
            response = self.client.get(reverse("chore_calendar"))
        self.assertContains(response, done.title)
        self.assertEqual(count_class(response, "calendar-on-time"), 1)
        self.assertEqual(count_class(response, "calendar-overdue"), 0)

    def test_no_due_date_chore_omitted(self):
        Chore.objects.create(title="No date", household=self.household)
        response = self.client.get(reverse("chore_calendar"))
        self.assertNotContains(response, "No date")

    def test_foreign_household_chores_not_shown(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Foreign", household=self.other_household,
                due_date=date(2026, 9, 15),
            )
            response = self.client.get(reverse("chore_calendar"))
        self.assertNotContains(response, "Foreign")

    def test_different_month_chore_not_shown(self):
        with mock.patch(
            "django.utils.timezone.localdate", return_value=date(2026, 9, 15)
        ):
            Chore.objects.create(
                title="Other month", household=self.household,
                due_date=date(2026, 10, 1),
            )
            response = self.client.get(reverse("chore_calendar"))
        self.assertNotContains(response, "Other month")
