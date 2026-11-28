from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import SimpleTestCase
from django.utils import timezone

from datetime import timedelta
from apps.events.tests import EventTestBase, make_event
from .models import BoothApplication, BoothTier
from .forms import BoothApplicationForm
from .selectors import events_needing_vendors, open_booth_tiers

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

from .selectors import events_needing_vendors, open_booth_tiers


class QueryFeatureTests(EventTestBase):
    def test_booth_directory_joins_event_and_district(self):
        event = make_event(self.organizer, self.venue)
        make_tier(event)
        with self.assertNumQueries(1):
            rows = list(open_booth_tiers())
            self.assertEqual(rows[0].event.venue.district.name, "Cebu City")

    def test_needs_vendors_excludes_tiers_with_applications(self):
        event = make_event(self.organizer, self.venue)
        tier = make_tier(event)
        self.assertEqual(list(events_needing_vendors(self.organizer)), [event])
        vendor = User.objects.create_user("ven", password="pw-12345-test", role="VENDOR")
        BoothApplication.objects.create(booth_tier=tier, vendor=vendor, product_description="x")
        self.assertEqual(list(events_needing_vendors(self.organizer)), [])

class CancelledEventGuardTests(EventTestBase):
    def test_cannot_add_tier_to_cancelled_event(self):
        event = make_event(self.organizer, self.venue, status="CANCELLED")
        self.client.force_login(self.organizer)
        url = reverse("vendors:tier_create", args=[event.slug])
        data = {"name": "Late", "booth_category": "DRY_GOODS", "max_width_m": "2",
                "max_depth_m": "2", "power_watts": 0, "fee": "100", "slots_total": 1,
                "guidelines": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BoothTier.objects.count(), 0)


class NavTests(EventTestBase):
    def test_needs_vendors_link_only_for_organizers(self):
        link = reverse("vendors:needs_vendors")
        self.client.force_login(self.attendee)
        self.assertNotContains(self.client.get(reverse("home:home")), link)
        self.client.force_login(self.organizer)
        self.assertContains(self.client.get(reverse("home:home")), link)

class BoothApplicationFormTests(SimpleTestCase):
    def test_valid_description(self):
        form = BoothApplicationForm({"product_description": "Hand-poured soy candles"})
        self.assertTrue(form.is_valid())

    def test_short_description_is_rejected(self):
        form = BoothApplicationForm({"product_description": "too short"})
        self.assertFalse(form.is_valid())
        self.assertIn("at least 10 characters", form.errors["product_description"][0])

    def test_blank_description_is_rejected(self):
        form = BoothApplicationForm({"product_description": "          "})
        self.assertFalse(form.is_valid())

    def test_description_is_stripped(self):
        form = BoothApplicationForm({"product_description": "  Hand-poured soy candles  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["product_description"], "Hand-poured soy candles")

class ApplicationTestBase(EventTestBase):
    def setUp(self):
        self.event = make_event(self.organizer, self.venue)
        self.tier = make_tier(self.event, slots_total=1)
        self.vendor = User.objects.create_user("ven", password="pw-12345-test", role="VENDOR")
        self.vendor.profile.business_or_stage_name = "Kiko Candles"
        self.vendor.profile.save()
        self.apply_url = reverse("vendors:apply", args=[self.tier.pk])
        self.list_url = reverse("vendors:my_applications")

    def apply(self, description="Hand-poured soy candles"):
        return self.client.post(self.apply_url, {"product_description": description})


class ApplyTests(ApplicationTestBase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.apply()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertEqual(BoothApplication.objects.count(), 0)

    def test_attendee_and_organizer_cannot_apply(self):
        for user in (self.attendee, self.organizer):
            self.client.force_login(user)
            self.assertEqual(self.apply().status_code, 302)
        self.assertEqual(BoothApplication.objects.count(), 0)

    def test_vendor_can_apply(self):
        self.client.force_login(self.vendor)
        response = self.apply()
        self.assertRedirects(response, self.list_url, fetch_redirect_response=False)
        application = BoothApplication.objects.get()
        self.assertEqual(application.vendor, self.vendor)
        self.assertEqual(application.booth_tier, self.tier)
        self.assertEqual(application.status, "PENDING")

    def test_duplicate_application_is_rejected(self):
        self.client.force_login(self.vendor)
        self.apply()
        response = self.apply("A different description here")
        self.assertRedirects(response, self.list_url, fetch_redirect_response=False)
        self.assertEqual(BoothApplication.objects.count(), 1)
        self.assertEqual(BoothApplication.objects.get().product_description,
                         "Hand-poured soy candles")

    def test_applying_beyond_capacity_is_allowed(self):
        other = User.objects.create_user("ven2", password="pw-12345-test", role="VENDOR")
        BoothApplication.objects.create(booth_tier=self.tier, vendor=other,
                                        product_description="Taken slot", status="APPROVED")
        self.client.force_login(self.vendor)
        self.apply()
        self.assertEqual(BoothApplication.objects.filter(booth_tier=self.tier).count(), 2)

    def test_unpublished_event_returns_404(self):
        draft = make_event(self.organizer, self.venue, title="Draft", slug="draft", status="DRAFT")
        tier = make_tier(draft)
        self.client.force_login(self.vendor)
        response = self.client.post(reverse("vendors:apply", args=[tier.pk]),
                                    {"product_description": "Hand-poured soy candles"})
        self.assertEqual(response.status_code, 404)

    def test_ended_event_is_refused(self):
        past = timezone.now() - timedelta(days=2)
        old = make_event(self.organizer, self.venue, title="Old", slug="old",
                         start_at=past, end_at=past + timedelta(hours=3))
        tier = make_tier(old)
        self.client.force_login(self.vendor)
        response = self.client.post(reverse("vendors:apply", args=[tier.pk]),
                                    {"product_description": "Hand-poured soy candles"})
        self.assertRedirects(response, reverse("events:detail", args=[old.slug]),
                             fetch_redirect_response=False)
        self.assertEqual(BoothApplication.objects.count(), 0)

    def test_my_applications_redirects_non_vendors(self):
        self.client.force_login(self.attendee)
        self.assertEqual(self.client.get(self.list_url).status_code, 302)


class WithdrawTests(ApplicationTestBase):
    def make_application(self, **overrides):
        fields = dict(booth_tier=self.tier, vendor=self.vendor,
                      product_description="Hand-poured soy candles")
        fields.update(overrides)
        return BoothApplication.objects.create(**fields)

    def test_withdraw_marks_withdrawn(self):
        application = self.make_application()
        self.client.force_login(self.vendor)
        self.client.post(reverse("vendors:withdraw", args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, "WITHDRAWN")

    def test_withdraw_requires_post(self):
        application = self.make_application()
        self.client.force_login(self.vendor)
        response = self.client.get(reverse("vendors:withdraw", args=[application.pk]))
        self.assertEqual(response.status_code, 405)

    def test_cannot_withdraw_someone_elses_application(self):
        application = self.make_application()
        other = User.objects.create_user("ven2", password="pw-12345-test", role="VENDOR")
        self.client.force_login(other)
        response = self.client.post(reverse("vendors:withdraw", args=[application.pk]))
        self.assertEqual(response.status_code, 404)
        application.refresh_from_db()
        self.assertEqual(application.status, "PENDING")

    def test_rejected_application_cannot_be_withdrawn(self):
        application = self.make_application(status="REJECTED")
        self.client.force_login(self.vendor)
        self.client.post(reverse("vendors:withdraw", args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, "REJECTED")

    def test_withdrawn_application_is_reopened_not_duplicated(self):
        application = self.make_application(status="WITHDRAWN", reviewed_at=timezone.now())
        self.client.force_login(self.vendor)
        self.apply("Updated candle and soap range")
        self.assertEqual(BoothApplication.objects.count(), 1)
        application.refresh_from_db()
        self.assertEqual(application.status, "PENDING")
        self.assertIsNone(application.reviewed_at)
        self.assertEqual(application.product_description, "Updated candle and soap range")

    def test_withdrawing_approved_application_frees_the_slot(self):
        application = self.make_application(status="APPROVED")
        self.client.force_login(self.vendor)
        self.client.post(reverse("vendors:withdraw", args=[application.pk]))
        response = self.client.get(reverse("events:detail", args=[self.event.slug]))
        self.assertEqual(response.context["booth_tiers"][0].remaining, 1)


class ApplicationPageTests(ApplicationTestBase):
    def make_application(self, **overrides):
        fields = dict(booth_tier=self.tier, vendor=self.vendor,
                      product_description="Hand-poured soy candles")
        fields.update(overrides)
        return BoothApplication.objects.create(**fields)

    def test_apply_form_shows_tier_and_business_name(self):
        self.client.force_login(self.vendor)
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tier.name)
        self.assertContains(response, "Kiko Candles")

    def test_blank_business_name_blocks_application(self):
        self.vendor.profile.business_or_stage_name = ""
        self.vendor.profile.save()
        self.client.force_login(self.vendor)
        response = self.apply()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add your business name")
        self.assertEqual(BoothApplication.objects.count(), 0)

    def test_short_description_shows_error(self):
        self.client.force_login(self.vendor)
        response = self.apply("too short")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "at least 10 characters")
        self.assertEqual(BoothApplication.objects.count(), 0)

    def test_my_applications_lists_only_own_rows(self):
        other = User.objects.create_user("ven2", password="pw-12345-test", role="VENDOR")
        self.make_application()
        self.make_application(vendor=other, product_description="Not mine at all")
        self.client.force_login(self.vendor)
        response = self.client.get(self.list_url)
        self.assertEqual([a.vendor for a in response.context["applications"]], [self.vendor])

    def test_my_applications_empty_state(self):
        self.client.force_login(self.vendor)
        self.assertContains(self.client.get(self.list_url), "No applications yet")

    def test_pending_row_has_withdraw_button(self):
        application = self.make_application()
        self.client.force_login(self.vendor)
        self.assertContains(self.client.get(self.list_url),
                            reverse("vendors:withdraw", args=[application.pk]))

    def test_withdrawn_row_offers_reapply(self):
        self.make_application(status="WITHDRAWN")
        self.client.force_login(self.vendor)
        self.assertContains(self.client.get(self.list_url), self.apply_url)