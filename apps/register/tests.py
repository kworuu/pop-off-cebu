from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegisterTests(TestCase):
    def submit(self, **overrides):
        data = {
            "username": "kiko", "email": "kiko@example.com", "role": "VENDOR",
            "password": "Str0ng-pass-91", "confirm_password": "Str0ng-pass-91",
        }
        data.update(overrides)
        return self.client.post(reverse("register:register"), data)

    def test_weak_password_is_rejected(self):
        response = self.submit(password="12345678", confirm_password="12345678")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="kiko").exists())

    def test_mismatched_passwords_are_rejected(self):
        response = self.submit(confirm_password="Different-pass-12")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="kiko").exists())

    def test_valid_registration_creates_user_and_profile(self):
        response = self.submit()
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="kiko")
        self.assertEqual(user.profile.district.slug, "cebu_city")
        self.assertEqual(user.role, "VENDOR")