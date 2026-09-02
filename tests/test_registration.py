from django.contrib.auth.models import User
from django.test import Client, TestCase


class RegistrationViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page_renders_form(self):
        response = self.client.get("/register/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="email"')

    def test_successful_registration_creates_user(self):
        response = self.client.post("/register/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongP@ss123",
            "password2": "StrongP@ss123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/onboarding/")
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@example.com")

    def test_successful_registration_logs_in_user(self):
        self.client.post("/register/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongP@ss123",
            "password2": "StrongP@ss123",
        })
        response = self.client.get("/onboarding/")
        self.assertEqual(response.status_code, 200)

    def test_duplicate_username_rejected(self):
        User.objects.create_user("existing", "existing@example.com", "password123!")
        response = self.client.post("/register/", {
            "username": "existing",
            "email": "new@example.com",
            "password1": "StrongP@ss123",
            "password2": "StrongP@ss123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_mismatched_passwords_rejected(self):
        response = self.client.post("/register/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongP@ss123",
            "password2": "DifferentP@ss456",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_weak_password_rejected(self):
        response = self.client.post("/register/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "123",
            "password2": "123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_authenticated_user_redirected(self):
        User.objects.create_user("user", "user@example.com", "password123!")
        self.client.login(username="user", password="password123!")
        response = self.client.get("/register/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
