import json
import time

from django.utils.deprecation import MiddlewareMixin

from .models import EndpointLog
from .services import get_client_ip, get_user_agent


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para capturar información de auditoría en cada request.
    Agrega atributos al request que pueden ser usados por las vistas.
    """

    def process_request(self, request):
        # Agregar información del cliente al request para que esté disponible
        request.audit_ip = get_client_ip(request)
        request.audit_user_agent = get_user_agent(request)
        request._start_time = time.perf_counter()
        return None


class ApiLoggingMiddleware(MiddlewareMixin):
    """Middleware para registrar cada request HTTP en EndpointLog."""

    def process_response(self, request, response):
        try:
            # Saltar endpoints no API (static, media, etc)
            if not request.path.startswith('/api/'):
                return response

            duration_ms = None
            if hasattr(request, '_start_time'):
                duration_ms = round((time.perf_counter() - request._start_time) * 1000, 2)

            user = getattr(request, 'user', None)
            company = getattr(user, 'company', None) if user and user.is_authenticated else None

            # Intentar serializar body/response a JSON de forma segura
            body_json = None
            try:
                if request.body and request.method in ['POST', 'PUT', 'PATCH']:
                    body_json = json.loads(request.body.decode('utf-8'))
            except Exception:
                body_json = None

            resp_json = None
            try:
                if hasattr(response, 'data'):
                    resp_json = response.data
            except Exception:
                resp_json = None

            EndpointLog.objects.create(
                user=user if user and user.is_authenticated else None,
                company=company if company and getattr(company, 'id', None) else None,
                method=request.method,
                path=request.get_full_path(),
                status_code=getattr(response, 'status_code', 0),
                duration_ms=duration_ms,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                request_body=body_json,
                response_body=resp_json,
            )
        except Exception:
            # No interrumpir la petición por errores de logging
            pass
        return response
