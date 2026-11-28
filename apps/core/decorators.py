"""Role guards shared by every feature slice.

Lives in `core` so slices such as `vendors` and `gigs` never have to import
another slice's views just to reuse a decorator. Role strings match
`accounts.User.Role`.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role, denied_message):
    """Require a logged-in user with `role`. Others are sent to the events
    list with an error message (anonymous users go to login first)."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, denied_message)
                return redirect("events:list")
            return view(request, *args, **kwargs)

        return login_required(wrapper)

    return decorator


organizer_required = role_required("ORGANIZER", "Only event organizers can do that.")
vendor_required = role_required("VENDOR", "Only vendors can do that.")