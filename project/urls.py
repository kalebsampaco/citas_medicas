from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Citas Médicas API",
        default_version="v1",
        description="API para gestión de citas médicas",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@citasmedicas.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/patients/", include("apps.patients.urls")),
    path("api/doctors/", include("apps.doctors.urls")),
    # Expose clinics and rooms at /api/clinics/ and /api/rooms/
    path("api/", include("apps.clinics.urls")),
    path("api/schedules/", include("apps.schedules.urls")),
    # Acepta /api/appointments y /api/appointments/
    re_path(r"^api/appointments/?", include("apps.appointments.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/chat/", include("apps.chat.urls")),
    # Swagger
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
