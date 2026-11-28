from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.events.constants import EVENT_CANCELLED
from apps.events.models import Event
from apps.core.decorators import organizer_required
from .forms import BoothTierForm
from .models import BoothTier
from .selectors import events_needing_vendors, open_booth_tiers, tiers_with_applications
from apps.core.decorators import vendor_required   # extend your existing core.decorators import line
from apps.events.constants import EVENT_PUBLISHED  # extend your existing events.constants import line
from .constants import (
    ACTIVE_APPLICATION_STATUSES, APPLICATION_PENDING, APPLICATION_WITHDRAWN,
)
from .forms import BoothApplicationForm  # extend your existing .forms import line
from .models import BoothApplication     # extend your existing .models import line

@organizer_required
def tier_create(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    if event.status == EVENT_CANCELLED:
        messages.error(request, "This event is cancelled, so you can't add booth tiers to it.")
        return redirect("events:detail", slug=slug)
    form = BoothTierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tier = form.save(commit=False)
        tier.event = event
        tier.save()
        form.save_m2m()
        messages.success(request, "Booth tier added.")
        return redirect("events:detail", slug=slug)
    return render(request, "vendors/tier_form.html", {"form": form, "event": event, "tier": None})

@organizer_required
def tier_edit(request, pk):
    tier = get_object_or_404(BoothTier.objects.select_related("event"), pk=pk, event__organizer=request.user)
    form = BoothTierForm(request.POST or None, instance=tier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Booth tier updated.")
        return redirect("events:detail", slug=tier.event.slug)
    return render(request, "vendors/tier_form.html", {"form": form, "event": tier.event, "tier": tier})


@organizer_required
@require_POST
def tier_delete(request, pk):
    tier = get_object_or_404(BoothTier.objects.select_related("event"), pk=pk, event__organizer=request.user)
    slug = tier.event.slug
    if tier.applications.exists():
        messages.error(request, "This tier has applications. Reject or withdraw them before deleting it.")
    else:
        tier.delete()
        messages.success(request, "Booth tier deleted.")
    return redirect("events:detail", slug=slug)

def booth_directory(request):
    return render(request, "vendors/booth_directory.html", {"tiers": open_booth_tiers()})


@organizer_required
def needs_vendors(request):
    return render(request, "vendors/needs_vendors.html",
                  {"events": events_needing_vendors(request.user)})

@vendor_required
def apply_to_tier(request, pk):
    tier = get_object_or_404(
        BoothTier.objects.select_related("event__venue__district"),
        pk=pk, event__status=EVENT_PUBLISHED,
    )
    event = tier.event
    if event.end_at < timezone.now():
        messages.error(request, "This event has already ended.")
        return redirect("events:detail", slug=event.slug)

    existing = BoothApplication.objects.filter(booth_tier=tier, vendor=request.user).first()
    if existing and existing.status != APPLICATION_WITHDRAWN:
        messages.error(request, "You already applied to this booth tier.")
        return redirect("vendors:my_applications")

    # A withdrawn application is re-opened (same row) instead of duplicated.
    profile_incomplete = not request.user.profile.business_or_stage_name.strip()
    form = BoothApplicationForm(request.POST or None, instance=existing)
    if request.method == "POST" and form.is_valid():
        if profile_incomplete:
            messages.error(request, "Add your business name in Settings before applying.")
        else:
            application = form.save(commit=False)
            application.booth_tier = tier
            application.vendor = request.user
            application.status = APPLICATION_PENDING
            application.reviewed_at = None
            application.save()
            messages.success(request, "Application submitted.")
            return redirect("vendors:my_applications")
    return render(request, "vendors/apply_form.html", {
        "form": form, "tier": tier, "event": event, "profile_incomplete": profile_incomplete,
    })


@vendor_required
def my_applications(request):
    applications = (
        BoothApplication.objects.filter(vendor=request.user)
        .select_related("booth_tier__event__venue__district")
        .order_by("-applied_at")
    )
    return render(request, "vendors/my_applications.html", {
        "applications": applications,
        "active_statuses": ACTIVE_APPLICATION_STATUSES,
        "now": timezone.now(),
    })


@vendor_required
@require_POST
def withdraw_application(request, pk):
    application = get_object_or_404(BoothApplication, pk=pk, vendor=request.user)
    if application.status in ACTIVE_APPLICATION_STATUSES:
        application.status = APPLICATION_WITHDRAWN
        application.save(update_fields=["status"])
        messages.success(request, "Application withdrawn.")
    else:
        messages.error(request, "This application can't be withdrawn.")
    return redirect("vendors:my_applications")


# --------------------------------------------------------- organizer review

@organizer_required
def event_applications(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    return render(request, "vendors/event_applications.html", {
        "event": event,
        "tiers": tiers_with_applications(event),
    })