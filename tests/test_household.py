from django.core.exceptions import ValidationError
from django.test import TestCase

from households.models import Household


class HouseholdModelTest(TestCase):
    def test_create_household(self):
        household = Household.objects.create(name="The Smiths")
        self.assertEqual(household.name, "The Smiths")
        self.assertIsNotNone(household.created_at)
        self.assertEqual(Household.objects.count(), 1)

    def test_empty_name_rejected(self):
        household = Household(name="")
        with self.assertRaises(ValidationError):
            household.full_clean()

    def test_whitespace_only_name_rejected(self):
        household = Household(name="   ")
        with self.assertRaises(ValidationError):
            household.full_clean()

    def test_str_representation(self):
        household = Household.objects.create(name="The Johnsons")
        self.assertEqual(str(household), "The Johnsons")

    def test_invite_code_auto_generated_and_unique(self):
        h1 = Household.objects.create(name="A")
        h2 = Household.objects.create(name="B")
        self.assertTrue(h1.invite_code)
        self.assertTrue(h2.invite_code)
        self.assertNotEqual(h1.invite_code, h2.invite_code)
