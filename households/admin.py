from django.contrib import admin

from households.models import Household, HouseholdMember


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "created_at")
    search_fields = ("name", "invite_code")
    actions = ["regenerate_invite_code"]

    @admin.action(description="Regenerate invite code")
    def regenerate_invite_code(self, request, queryset):
        count = queryset.count()
        for household in queryset:
            household.invite_code = Household.generate_invite_code()
            household.save(update_fields=["invite_code"])
        self.message_user(request, f"Regenerated invite code for {count} household(s).")


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = ("household", "user", "joined_at")
