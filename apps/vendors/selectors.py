from django.db.models import Count, Prefetch, Q, Subquery
from django.utils import timezone

from apps.events.constants import EVENT_PUBLISHED
from apps.events.models import Event
from .models import BoothApplication, BoothTier


def open_booth_tiers():
    """JOIN: booth tier + event + venue + district in one query."""
    return (
        BoothTier.objects
        .select_related("event__venue__district")
        .filter(event__status=EVENT_PUBLISHED, event__end_at__gte=timezone.now())
        .order_by("event__start_at", "fee")
    )


def events_needing_vendors(organizer):
    """SUBQUERY: events with at least one tier that has no applications."""
    tiers_with_applications = BoothApplication.objects.values("booth_tier_id")
    event_ids = (
        BoothTier.objects
        .exclude(id__in=Subquery(tiers_with_applications))
        .values("event_id")
    )
    return (
        Event.objects
        .filter(organizer=organizer, id__in=Subquery(event_ids))
        .select_related("venue__district")
        .order_by("start_at")
    )


def tiers_with_applications(event):
    """Booth tiers of one event, each with its applications (oldest first) and an
    `approved` count. Two queries in total, however many applications exist."""
    applications = BoothApplication.objects.select_related("vendor__profile").order_by("applied_at")
    return (
        BoothTier.objects.filter(event=event)
        .annotate(approved=Count("applications", filter=Q(applications__status="APPROVED")))
        .prefetch_related(Prefetch("applications", queryset=applications))
    )