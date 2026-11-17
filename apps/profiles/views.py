from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.events.constants import RSVP_SAVED
from apps.events.models import Event


@login_required
def profile_view(request):
    user = request.user

    # Each role gets a label and a function that counts its real records.
    # Only the current user's role is evaluated, so we run one query.
    stats_map = {
        "ORGANIZER": ("Events Hosted", lambda: Event.objects.filter(organizer=user).count()),
        "VENDOR": ("Booth Applications", lambda: user.booth_applications.count()),
        "PERFORMER": ("Gig Applications", lambda: user.gig_applications.count()),
        "ATTENDEE": ("Saved Events", lambda: user.rsvps.filter(status=RSVP_SAVED).count()),
    }
    label, count = stats_map.get(user.role, ("Platform Activities", lambda: 0))

    return render(request, "profiles/profile.html", {
        "profile": user.profile,
        "stat": {"label": label, "value": count()},
    })