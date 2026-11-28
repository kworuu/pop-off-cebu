from django.urls import path
from . import views

app_name = "vendors"

urlpatterns = [
    path("events/<slug:slug>/tiers/new/", views.tier_create, name="tier_create"),
    path("tiers/<int:pk>/edit/", views.tier_edit, name="tier_edit"),
    path("tiers/<int:pk>/delete/", views.tier_delete, name="tier_delete"),
    path("booths/", views.booth_directory, name="booth_directory"),
    path("needs-vendors/", views.needs_vendors, name="needs_vendors"),
    path("tiers/<int:pk>/apply/", views.apply_to_tier, name="apply"),
    path("applications/", views.my_applications, name="my_applications"),
    path("applications/<int:pk>/withdraw/", views.withdraw_application, name="withdraw"),
    path("events/<slug:slug>/applications/", views.event_applications, name="event_applications"),
        path("applications/<int:pk>/review/", views.review_application, name="review"),
]