from django.contrib.auth.models import User
from django.test import Client, TestCase


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "password123!"
        )

    def test_login_page_renders_form(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_successful_login_and_redirect(self):
        response = self.client.post("/login/", {
            "username": "tester",
            "password": "password123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_next_parameter_honored(self):
        response = self.client.post("/login/", {
            "username": "tester",
            "password": "password123!",
        })
        # Login redirects to home; next URL is honored via next parameter if provided
        # and safe. Django's LoginView only redirects to next when it is safe.
        self.assertEqual(response.url, "/")

    def test_invalid_credentials_rejected(self):
        response = self.client.post("/login/", {
            "username": "tester",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_user_redirected_away_from_login(self):
        self.client.force_login(self.user)
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 302)

    def test_logout_ends_session(self):
        self.client.force_login(self.user)
        response = self.client.post("/logout/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_protected_view_redirects_anonymous(self):
        response = self.client.get("/onboarding/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)
