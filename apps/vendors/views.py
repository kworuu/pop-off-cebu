from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.events.models import Event
from apps.events.views import organizer_required
from .forms import BoothTierForm
from .models import BoothTier


@organizer_required
def tier_create(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
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