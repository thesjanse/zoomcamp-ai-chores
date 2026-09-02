from django.contrib.auth.models import User
from django.test import Client, TestCase

from households.models import Household, HouseholdMember


class OnboardingFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )
        self.client.force_login(self.user)

    def test_onboarding_requires_login(self):
        self.client.logout()
        response = self.client.get("/onboarding/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_onboarding_renders_create_and_join_options(self):
        response = self.client.get("/onboarding/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create a New Household")
        self.assertContains(response, "Join via Invite Code")

    def test_create_household_links_user(self):
        response = self.client.post("/onboarding/", {
            "create": "1",
            "name": "The Smiths",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        household = Household.objects.get(name="The Smiths")
        self.assertTrue(
            HouseholdMember.objects.filter(
                user=self.user, household=household
            ).exists()
        )

    def test_join_via_invite_code_links_user(self):
        household = Household.objects.create(name="Existing House")
        response = self.client.post("/onboarding/", {
            "join": "1",
            "invite_code": household.invite_code,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertTrue(
            HouseholdMember.objects.filter(
                user=self.user, household=household
            ).exists()
        )

    def test_invalid_invite_code_does_not_link_user(self):
        response = self.client.post("/onboarding/", {
            "join": "1",
            "invite_code": "NOPE1234",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(HouseholdMember.objects.count(), 0)
        self.assertContains(response, "Invalid invite code")

    def test_user_with_household_redirected_away(self):
        household = Household.objects.create(name="Home")
        HouseholdMember.objects.create(user=self.user, household=household)
        response = self.client.get("/onboarding/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_full_flow_ends_up_linked(self):
        self.client.logout()
        response = self.client.post("/register/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongP@ss123",
            "password2": "StrongP@ss123",
        })
        self.assertEqual(response.url, "/onboarding/")
        onboarding_response = self.client.post("/onboarding/", {
            "create": "1",
            "name": "The Johnsons",
        })
        self.assertEqual(onboarding_response.status_code, 302)
        self.assertTrue(
            HouseholdMember.objects.filter(
                user__username="newuser", household__name="The Johnsons"
            ).exists()
        )
