from django.urls import reverse
from apps.events.tests import EventTestBase, make_event


class ProfileTests(EventTestBase):
    def test_requires_login(self):
        response = self.client.get(reverse("profiles:profile"))
        self.assertEqual(response.status_code, 302)

    def test_organizer_stat_counts_real_events(self):
        make_event(self.organizer, self.venue)
        make_event(self.organizer, self.venue, title="Second", slug="second")
        self.client.force_login(self.organizer)
        response = self.client.get(reverse("profiles:profile"))
        self.assertEqual(response.context["stat"], {"label": "Events Hosted", "value": 2})

    def test_attendee_stat_starts_at_zero(self):
        self.client.force_login(self.attendee)
        response = self.client.get(reverse("profiles:profile"))
        self.assertEqual(response.context["stat"]["value"], 0)