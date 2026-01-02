from django.urls import path

from .views import SendReminderView, WhatsAppWebhookView
from .views_test import TestWhatsAppView

urlpatterns = [
    path("whatsapp/send/<int:appointment_id>/", SendReminderView.as_view()),
    path("whatsapp/webhook/", WhatsAppWebhookView.as_view()),
    path("test-whatsapp/", TestWhatsAppView.as_view()),
]
