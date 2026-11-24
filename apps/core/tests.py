from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from .decorators import organizer_required, vendor_required

User = get_user_model()


def _request(user):
    request = RequestFactory().get("/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@organizer_required
def organizer_only(request):
    return HttpResponse("ok")


@vendor_required
def vendor_only(request):
    return HttpResponse("ok")


class RoleDecoratorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = User.objects.create_user("org", password="pw-12345-test", role="ORGANIZER")
        cls.vendor = User.objects.create_user("ven", password="pw-12345-test", role="VENDOR")

    def test_matching_role_passes(self):
        self.assertEqual(organizer_only(_request(self.organizer)).status_code, 200)
        self.assertEqual(vendor_only(_request(self.vendor)).status_code, 200)

    def test_wrong_role_is_redirected_with_message(self):
        request = _request(self.vendor)
        response = organizer_only(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual([str(m) for m in request._messages], ["Only event organizers can do that."])

    def test_anonymous_goes_to_login(self):
        # AnonymousUser has no `role`, so login_required must run before the role check.
        response = vendor_only(_request(AnonymousUser()))
        self.assertEqual(response.status_code, 302)