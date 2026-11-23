from django.contrib import admin

from .models import BoothApplication, BoothTier


@admin.register(BoothTier)
class BoothTierAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "booth_category", "fee", "slots_total")
    list_filter = ("booth_category",)
    search_fields = ("name", "event__title")


@admin.register(BoothApplication)
class BoothApplicationAdmin(admin.ModelAdmin):
    list_display = ("vendor", "booth_tier", "status", "applied_at")
    list_filter = ("status",)