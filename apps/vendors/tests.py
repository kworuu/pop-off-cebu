from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.events.tests import EventTestBase, make_event
from .models import BoothApplication, BoothTier

User = get_user_model()


def make_tier(event, **overrides):
    fields = dict(event=event, name="Dry goods", booth_category="DRY_GOODS",
                  max_width_m=2, max_depth_m=2, power_watts=0, fee=500, slots_total=2)
    fields.update(overrides)
    return BoothTier.objects.create(**fields)


class TierManagementTests(EventTestBase):
    def setUp(self):
        self.event = make_event(self.organizer, self.venue)
        self.create_url = reverse("vendors:tier_create", args=[self.event.slug])

    def payload(self, **overrides):
        data = {"name": "Hot food", "booth_category": "HOT_COOKING",
                "max_width_m": "3", "max_depth_m": "2", "power_watts": 800,
                "fee": "1500", "slots_total": 4, "guidelines": ""}
        data.update(overrides)
        return data

    def test_owner_can_create_tier(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.create_url, self.payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BoothTier.objects.filter(event=self.event).count(), 1)

    def test_attendee_cannot_create_tier(self):
        self.client.force_login(self.attendee)
        self.client.post(self.create_url, self.payload())
        self.assertEqual(BoothTier.objects.count(), 0)

    def test_other_organizer_gets_404(self):
        other = User.objects.create_user("org2", password="pw-12345-test", role="ORGANIZER")
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.create_url).status_code, 404)

    def test_invalid_dimensions_rejected(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.create_url, self.payload(max_width_m="0"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BoothTier.objects.count(), 0)

    def test_non_owner_cannot_edit(self):
        tier = make_tier(self.event)
        other = User.objects.create_user("org2", password="pw-12345-test", role="ORGANIZER")
        self.client.force_login(other)
        response = self.client.get(reverse("vendors:tier_edit", args=[tier.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_blocked_when_applications_exist(self):
        tier = make_tier(self.event)
        vendor = User.objects.create_user("ven", password="pw-12345-test", role="VENDOR")
        BoothApplication.objects.create(booth_tier=tier, vendor=vendor, product_description="Candles")
        self.client.force_login(self.organizer)
        self.client.post(reverse("vendors:tier_delete", args=[tier.pk]))
        self.assertTrue(BoothTier.objects.filter(pk=tier.pk).exists())

    def test_delete_works_without_applications(self):
        tier = make_tier(self.event)
        self.client.force_login(self.organizer)
        self.client.post(reverse("vendors:tier_delete", args=[tier.pk]))
        self.assertFalse(BoothTier.objects.filter(pk=tier.pk).exists())

    def test_detail_shows_remaining_slots(self):
        tier = make_tier(self.event, slots_total=2)
        vendor = User.objects.create_user("ven", password="pw-12345-test", role="VENDOR")
        BoothApplication.objects.create(booth_tier=tier, vendor=vendor,
                                        product_description="Candles", status="APPROVED")
        response = self.client.get(reverse("events:detail", args=[self.event.slug]))
        self.assertEqual(response.context["booth_tiers"][0].remaining, 1)