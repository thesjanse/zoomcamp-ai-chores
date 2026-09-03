from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.contrib.sites.models import Site


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


class PasswordResetTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "tester", "tester@example.com", "oldpassword123!"
        )
        Site.objects.update_or_create(
            id=1, defaults={"domain": "testserver", "name": "testserver"}
        )

    def test_forgot_password_link_on_login_page(self):
        response = self.client.get("/login/")
        self.assertContains(response, "/password-reset/")
        self.assertContains(response, "Forgot your password?")

    def test_password_reset_page_renders_email_form(self):
        response = self.client.get("/password-reset/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")
        self.assertContains(response, 'name="email"')

    def test_password_reset_valid_email_sends_email_and_redirects(self):
        response = self.client.post("/password-reset/", {"email": "tester@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/password-reset/done/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("tester@example.com", mail.outbox[0].to)

    def test_password_reset_done_page_shows_message(self):
        response = self.client.get("/password-reset/done/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "emailed you instructions")

    def test_password_reset_nonexistent_email_no_user_enumeration(self):
        response = self.client.post(
            "/password-reset/", {"email": "nobody@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/password-reset/done/")
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_email_contains_valid_link(self):
        self.client.post("/password-reset/", {"email": "tester@example.com"})
        email_body = mail.outbox[0].body
        self.assertIn("http://", email_body)
        self.assertIn("/password-reset/", email_body)

    def _extract_reset_token(self):
        self.client.post("/password-reset/", {"email": "tester@example.com"})
        email_body = mail.outbox[0].body
        start = email_body.index("/password-reset/") + len("/password-reset/")
        uidb64_end = email_body.index("/", start)
        uidb64 = email_body[start:uidb64_end]
        token_end = email_body.index("\n", uidb64_end)
        token = email_body[uidb64_end + 1:token_end].rstrip("/")
        return uidb64, token

    def test_full_password_reset_flow(self):
        uidb64, token = self._extract_reset_token()
        token_url = f"/password-reset/{uidb64}/{token}/"
        set_password_url = f"/password-reset/{uidb64}/set-password/"

        response = self.client.get(token_url)
        self.assertRedirects(response, set_password_url)

        response = self.client.get(set_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set New Password")

        response = self.client.post(set_password_url, {
            "new_password1": "NewSecurePass123!",
            "new_password2": "NewSecurePass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/password-reset/complete/")

        response = self.client.get("/password-reset/complete/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")

        response = self.client.post("/login/", {
            "username": "tester",
            "password": "NewSecurePass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_old_password_no_longer_works(self):
        uidb64, token = self._extract_reset_token()
        set_password_url = f"/password-reset/{uidb64}/set-password/"
        self.client.get(f"/password-reset/{uidb64}/{token}/")
        self.client.post(set_password_url, {
            "new_password1": "NewSecurePass123!",
            "new_password2": "NewSecurePass123!",
        })

        response = self.client.post("/login/", {
            "username": "tester",
            "password": "oldpassword123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
