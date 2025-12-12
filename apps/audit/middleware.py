from django.utils.deprecation import MiddlewareMixin

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
        return None
