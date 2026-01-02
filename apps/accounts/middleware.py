from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from .models.user_log import InvoiceUsageLog

class InvoiceQuotaMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not getattr(request.user, 'is_authenticated', False):
            return
        company = request.user.company
        if not company:
            return
        # Notificar si está cerca del límite
        if company.is_near_limit and not cache.get(f"quota_warning:{company.id}"):
            # Enviar notificación (email, webhook, etc)
            cache.set(f"quota_warning:{company.id}", True, timeout=3600)
            # TODO: Implementar envío de email/notificación
        request.company_quota_exceeded = company.is_over_limit