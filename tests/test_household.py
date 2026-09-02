import re
from unittest.mock import Mock

from django.contrib.admin import AdminSite
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from households.admin import HouseholdAdmin
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
        h3 = Household.objects.create(name="C")
        self.assertTrue(h1.invite_code)
        self.assertTrue(h2.invite_code)
        self.assertTrue(h3.invite_code)
        pattern = re.compile(r"^HOME-[A-Z0-9]{4}$")
        for h in (h1, h2, h3):
            self.assertRegex(h.invite_code, pattern)
        codes = {h1.invite_code, h2.invite_code, h3.invite_code}
        self.assertEqual(len(codes), 3)

    def test_duplicate_invite_code_rejected(self):
        h1 = Household.objects.create(name="X")
        duplicate = Household(name="Y", invite_code=h1.invite_code)
        with self.assertRaises(IntegrityError):
            duplicate.save()


class HouseholdAdminActionTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = HouseholdAdmin(Household, self.site)
        self.request = Mock()

    def test_regenerate_invite_code_single(self):
        household = Household.objects.create(name="The Smiths")
        old_code = household.invite_code

        self.admin.regenerate_invite_code(self.request, Household.objects.filter(pk=household.pk))

        new_code = Household.objects.get(pk=household.pk).invite_code
        self.assertNotEqual(new_code, old_code)
        self.assertRegex(new_code, re.compile(r"^HOME-[A-Z0-9]{4}$"))
        self.assertFalse(Household.objects.filter(invite_code=old_code).exists())
        self.request._messages.add.assert_called()

        refreshed = Household.objects.get(pk=household.pk)
        self.assertEqual(refreshed.name, "The Smiths")
        self.assertEqual(refreshed.created_at, household.created_at)

    def test_regenerate_invite_code_bulk(self):
        households = [
            Household.objects.create(name="A"),
            Household.objects.create(name="B"),
            Household.objects.create(name="C"),
        ]
        old_codes = [h.invite_code for h in households]

        self.admin.regenerate_invite_code(
            self.request, Household.objects.filter(pk__in=[h.pk for h in households])
        )

        new_codes = set(
            Household.objects.filter(pk__in=[h.pk for h in households]).values_list(
                "invite_code", flat=True
            )
        )
        self.assertEqual(len(new_codes), 3)
        for old_code in old_codes:
            self.assertNotIn(old_code, new_codes)
            self.assertFalse(Household.objects.filter(invite_code=old_code).exists())
