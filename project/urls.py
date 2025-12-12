from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/patients/", include("apps.patients.urls")),
    path("api/doctors/", include("apps.doctors.urls")),
    path("api/clinics/", include("apps.clinics.urls")),
    path("api/schedules/", include("apps.schedules.urls")),
    path("api/appointments/", include("apps.appointments.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]
