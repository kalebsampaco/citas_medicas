from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin

class IsCompanyAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_super_admin or request.user.is_company_admin)

class IsCompanyAdminOrReadOnly(permissions.BasePermission):
    """Permite lectura (GET) para usuarios autenticados de la empresa, escritura solo para admin."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Lectura permitida para cualquier usuario autenticado de la empresa
        if request.method in permissions.SAFE_METHODS:
            return bool(getattr(request.user, 'company', None))
        # Escritura solo para admin
        return request.user.is_super_admin or request.user.is_company_admin

class HasPermission(permissions.BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        perm = getattr(view, 'required_permission', self.required_permission)
        if not perm:
            return True
        return request.user.has_permission(perm)

class HasInvoiceQuota(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.company:
            return False
        return not request.user.company.is_over_limit

class IsPaymentActiveOrSuperAdmin(permissions.BasePermission):
    message = "Pago mensual no registrado. Acceso bloqueado hasta regularizar el pago."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_super_admin', False):
            return True
        company = getattr(user, 'company', None)
        if not company:
            return False
        return bool(getattr(company, 'is_payment_active', False))
