from django.contrib import admin

from households.models import Household, HouseholdMember


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "created_at")
    search_fields = ("name", "invite_code")


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = ("household", "user", "joined_at")
