from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from chores.models import Chore
from households.models import Household, HouseholdMember


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
