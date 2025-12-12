from django.urls import path

from .views import SendReminderView, WhatsAppWebhookView

urlpatterns = [
    path("whatsapp/send/<int:appointment_id>/", SendReminderView.as_view()),
    path("whatsapp/webhook/", WhatsAppWebhookView.as_view()),
]
