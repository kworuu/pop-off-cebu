from django.urls import path
from . import views

app_name = "vendors"

urlpatterns = [
    path("events/<slug:slug>/tiers/new/", views.tier_create, name="tier_create"),
    path("tiers/<int:pk>/edit/", views.tier_edit, name="tier_edit"),
    path("tiers/<int:pk>/delete/", views.tier_delete, name="tier_delete"),
]