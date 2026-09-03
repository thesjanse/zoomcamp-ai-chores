import re
from unittest.mock import Mock

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from chores.models import Chore
from households.admin import HouseholdAdmin
from households.models import Household, HouseholdMember


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


class HouseholdMemberRoleTest(TestCase):
    def test_default_role_is_member(self):
        household = Household.objects.create(name="The Smiths")
        user = User.objects.create_user("joiner")
        member = HouseholdMember.objects.create(user=user, household=household)
        self.assertEqual(member.role, "member")

    def test_unique_together_preserved(self):
        household = Household.objects.create(name="The Smiths")
        user = User.objects.create_user("solo")
        HouseholdMember.objects.create(user=user, household=household)
        with self.assertRaises(IntegrityError):
            HouseholdMember.objects.create(user=user, household=household)

    def test_admin_choices_exact(self):
        self.assertCountEqual(
            [c[0] for c in HouseholdMember.Role.choices],
            ["admin", "member"],
        )

    def test_is_admin_property(self):
        household = Household.objects.create(name="The Smiths")
        admin = HouseholdMember.objects.create(
            user=User.objects.create_user("a"), household=household, role="admin"
        )
        member = HouseholdMember.objects.create(
            user=User.objects.create_user("m"), household=household, role="member"
        )
        self.assertTrue(admin.is_admin)
        self.assertFalse(member.is_admin)


class HouseholdMemberAdminListTest(TestCase):
    def test_list_display_includes_role(self):
        from households.admin import HouseholdMemberAdmin

        self.assertIn("role", HouseholdMemberAdmin.list_display)


class HouseholdMembersManageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            "admin", "admin@example.com", "password123!"
        )
        self.household = Household.objects.create(name="The Smiths")
        self.admin_membership = HouseholdMember.objects.create(
            user=self.admin, household=self.household, role="admin"
        )
        self.client.force_login(self.admin)

        self.member_user = User.objects.create_user("member")
        self.member_membership = HouseholdMember.objects.create(
            user=self.member_user, household=self.household, role="member"
        )

        self.other_user = User.objects.create_user("other")
        self.other_household = Household.objects.create(name="The Others")
        HouseholdMember.objects.create(
            user=self.other_user, household=self.other_household, role="admin"
        )

    def test_onboarding_create_sets_creator_admin(self):
        self.client.logout()
        new_admin = User.objects.create_user("creator")
        self.client.force_login(new_admin)
        response = self.client.post(reverse("onboarding"), {
            "create": "1",
            "name": "New House",
        })
        self.assertEqual(response.status_code, 302)
        membership = HouseholdMember.objects.get(
            user=new_admin, household=Household.objects.get(name="New House")
        )
        self.assertEqual(membership.role, "admin")

    def test_onboarding_join_sets_joiner_member(self):
        self.client.logout()
        joiner = User.objects.create_user("joiner")
        self.client.force_login(joiner)
        response = self.client.post(reverse("onboarding"), {
            "join": "1",
            "invite_code": self.household.invite_code,
        })
        self.assertEqual(response.status_code, 302)
        membership = HouseholdMember.objects.get(user=joiner, household=self.household)
        self.assertEqual(membership.role, "member")

    def test_members_page_lists_username_and_role(self):
        response = self.client.get(reverse("household_members"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin.username)
        self.assertContains(response, self.member_user.username)
        self.assertContains(response, "Make Member")
        self.assertContains(response, "Make Admin")

    def test_member_gets_403_on_members_page(self):
        self.client.force_login(self.member_user)
        response = self.client.get(reverse("household_members"))
        self.assertEqual(response.status_code, 403)

    def test_member_gets_403_on_settings(self):
        self.client.force_login(self.member_user)
        response = self.client.get(reverse("household_settings"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_settings(self):
        response = self.client.get(reverse("household_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.household.name)

    def test_anonymous_redirected_to_login_on_members(self):
        self.client.logout()
        response = self.client.get(reverse("household_members"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_anonymous_redirected_to_login_on_promote(self):
        self.client.logout()
        response = self.client.post(
            reverse("member_promote", args=[self.member_membership.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_no_household_user_redirected_to_onboarding(self):
        no_house = User.objects.create_user("homeless")
        self.client.force_login(no_house)
        response = self.client.get(reverse("household_members"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding"))

    def test_admin_promotes_member(self):
        response = self.client.post(
            reverse("member_promote", args=[self.member_membership.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "admin")

    def test_admin_demotes_admin(self):
        response = self.client.post(
            reverse("member_demote", args=[self.member_membership.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "member")

    def test_member_forbidden_from_promote(self):
        self.client.force_login(self.member_user)
        response = self.client.post(
            reverse("member_promote", args=[self.admin_membership.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "admin")

    def test_member_forbidden_from_demote(self):
        self.client.force_login(self.member_user)
        response = self.client.post(
            reverse("member_demote", args=[self.admin_membership.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "admin")

    def test_member_cannot_self_promote(self):
        self.client.force_login(self.member_user)
        response = self.client.post(
            reverse("member_promote", args=[self.member_membership.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "member")

    def test_last_admin_cannot_be_demoted(self):
        response = self.client.post(
            reverse("member_demote", args=[self.admin_membership.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "admin")

    def test_admin_can_demote_admin_when_another_admin_exists(self):
        other_admin = User.objects.create_user("other_admin")
        HouseholdMember.objects.create(
            user=other_admin, household=self.household, role="admin"
        )
        response = self.client.post(
            reverse("member_demote", args=[self.admin_membership.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "member")

    def test_foreign_household_promote_404(self):
        foreign = HouseholdMember.objects.create(
            user=User.objects.create_user("foreign_too"),
            household=self.other_household,
            role="member",
        )
        response = self.client.post(reverse("member_promote", args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.role, "member")

    def test_foreign_household_demote_404(self):
        foreign = HouseholdMember.objects.create(
            user=User.objects.create_user("foreign_member"),
            household=self.other_household,
            role="admin",
        )
        response = self.client.post(reverse("member_demote", args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.role, "admin")

    def test_promote_idempotent(self):
        response = self.client.post(
            reverse("member_promote", args=[self.admin_membership.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "admin")

    def test_demote_member_idempotent(self):
        response = self.client.post(
            reverse("member_demote", args=[self.member_membership.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "member")

    def test_role_change_does_not_affect_chore_assignments(self):
        chore = Chore.objects.create(
            title="Assigned chore",
            household=self.household,
            assigned_to=self.member_user,
            status="in_progress",
        )
        self.client.post(
            reverse("member_promote", args=[self.member_membership.pk])
        )
        chore.refresh_from_db()
        self.assertEqual(chore.assigned_to, self.member_user)
        self.assertEqual(chore.status, "in_progress")

    def test_role_change_preserves_other_membership_fields(self):
        original_user = self.member_membership.user
        original_household = self.member_membership.household
        original_joined = self.member_membership.joined_at
        self.client.post(
            reverse("member_promote", args=[self.member_membership.pk])
        )
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.user, original_user)
        self.assertEqual(self.member_membership.household, original_household)
        self.assertEqual(self.member_membership.joined_at, original_joined)

    def test_member_can_view_chores_and_claim(self):
        self.client.force_login(self.member_user)
        chore = Chore.objects.create(
            title="Claimable", household=self.household
        )
        list_response = self.client.get(reverse("chore_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, chore.title)

        claim_response = self.client.post(reverse("chore_claim", args=[chore.pk]))
        self.assertEqual(claim_response.status_code, 200)
        chore.refresh_from_db()
        self.assertEqual(chore.assigned_to, self.member_user)
        self.assertEqual(chore.status, "in_progress")
