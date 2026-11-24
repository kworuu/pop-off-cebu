from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", include("apps.login.urls")),
    path("register/", include("apps.register.urls")),
    path("profiles/", include("apps.profiles.urls")),
    path("settings/", include("apps.user_settings.urls")),
    path("events/", include("apps.events.urls")),
    path("vendors/", include("apps.vendors.urls")),
    path("", include("apps.home.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)