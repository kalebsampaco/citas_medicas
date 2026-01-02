from apps.appointments.models import Appointment
from apps.clinics.models import Room
from django.db.models import Count, F, Q, Sum
from django.utils.crypto import get_random_string
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models.company import Company
from ..models.plan import Plan
from ..models.plan_payment import PlanPayment
from ..models.role import Role
from ..models.user import User
from ..models.user_log import InvoiceUsageLog
from ..permissions import IsCompanyAdmin, IsSuperAdmin
from ..serializers.admin import (CompanyCreateResponseSerializer,
                                 CompanySerializer, DashboardStatsSerializer,
                                 PlanPaymentSerializer, PlanSerializer,
                                 RoleSerializer, UserSerializer)
from ..utils.email import send_admin_credentials_email


class PlanViewSet(viewsets.ModelViewSet):
    """Administración de planes (solo Super Admin)."""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [IsSuperAdmin]

    @swagger_auto_schema(
        operation_summary="Listar planes",
        tags=["Plans"],
        responses={
            200: openapi.Response(description="OK"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Obtener plan",
        tags=["Plans"],
        responses={
            200: PlanSerializer,
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Crear plan",
        tags=["Plans"],
        request_body=PlanSerializer,
        responses={
            201: PlanSerializer,
            400: openapi.Response(description="Solicitud inválida"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        },
        examples=[
            {
                "name": "Plan Estándar",
                "summary": "Crear plan con límites y features",
                "value": {
                    "name": "Standard",
                    "plan_type": "STANDARD",
                    "max_invoices": 1000,
                    "max_users": 10,
                    "max_roles": 5,
                    "price_monthly": 29.99,
                    "is_active": True,
                    "features": {
                        "reports": True,
                        "api_access": False
                    }
                }
            }
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Actualizar plan",
        tags=["Plans"],
        request_body=PlanSerializer,
        responses={
            200: PlanSerializer,
            400: openapi.Response(description="Solicitud inválida"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        },
        examples=[
            {
                "name": "Actualizar límites",
                "summary": "Incrementar límites de facturas y usuarios",
                "value": {
                    "max_invoices": 2000,
                    "max_users": 20
                }
            }
        ]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Eliminar plan",
        tags=["Plans"],
        responses={
            204: openapi.Response(description="Eliminado"),
            400: openapi.Response(description="Plan en uso"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Validar que el plan no esté en uso
        if Company.objects.filter(plan=instance).exists():
            return Response(
                {'detail': 'No se puede eliminar el plan porque está en uso por una o más empresas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        # Evitar ejecutar lógica de acceso durante la generación del esquema (usuario anónimo)
        if getattr(self, 'swagger_fake_view', False):
            return Company.objects.none()
        user = self.request.user
        if getattr(user, 'is_super_admin', False):
            return Company.objects.all()
        if getattr(user, 'company_id', None):
            return Company.objects.filter(id=user.company_id)
        return Company.objects.none()

    @swagger_auto_schema(
        operation_summary="Crear empresa",
        operation_description="Crea una empresa con límites derivados del plan y aprovisiona usuario admin inicial.\n\nDevuelve el objeto de empresa y las credenciales del admin inicial.",
        request_body=CompanySerializer,
        responses={
            201: CompanyCreateResponseSerializer,
            400: openapi.Response(description="Solicitud inválida")
        },
        examples=[
            {
                "name": "Empresa básica",
                "summary": "Crear empresa con plan y contraseña opcional",
                "value": {
                    "name": "Mi Empresa",
                    "rnc": "101234567",
                    "email": "admin@miempresa.com",
                    "phone": "+1 809-555-1234",
                    "address": "Av. Principal 123",
                    "dgii_certificate_uploaded": False,
                    "dgii_ambiente_default": "PROD",
                    "plan_id": 1,
                    "admin_password": "Admin123!"
                }
            }
        ],
        tags=["Companies"]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.validated_data.get('plan')
        if not plan:
            return Response({'plan_id': 'Este campo es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        # Crear la compañía con límites derivados del plan
        company = serializer.save(
            invoice_limit=plan.max_invoices,
            user_limit=plan.max_users,
            role_limit=plan.max_roles,
            clinic_limit=plan.max_clinics,
            plan=plan
        )
        # Aprovisionamiento automático: rol COMPANY_ADMIN y usuario inicial con permisos dinámicos
        features = plan.features or {}
        default_permissions = {
            'citas.create': True,
            'citas.view': True,
            'users.manage': True,
            'roles.manage': True
        }
        if features.get('reports'):
            default_permissions['reports.view'] = True
        if features.get('api_access'):
            default_permissions['api.access'] = True
        admin_role = Role.objects.create(
            company=company,
            name='Admin Empresa',
            role_type='COMPANY_ADMIN',
            permissions=default_permissions
        )
        # Permitir que el front defina la contraseña del admin; si no, generar una temporal
        admin_password = request.data.get('admin_password') or get_random_string(12)
        # El email de la empresa será el usuario con el que se loguea el admin inicial
        username = (company.email or f"admin_{company.rnc}").lower()
        admin_user = User(
            username=username,
            email=company.email or f"{username}@example.com",
            company=company,
            role=admin_role
        )
        admin_user.set_password(admin_password)
        admin_user.save()
        # Preparar respuesta extendida (estructura clara)
        payload = {
            'company': CompanySerializer(company).data,
            'initial_admin': {
                'username': admin_user.username,
                'password': admin_password,
            }
        }
        # ENVÍO DE CORREO CON ACS (Azure Communication Services)
        to_email = payload['company'].get('email')
        company_name = payload['company'].get('name') or 'Su Empresa'
        if to_email and payload['initial_admin']['username'] and payload['initial_admin']['password']:
            # Ignorar errores de envío, no bloquear la creación
            try:
                send_admin_credentials_email(
                    to_email,
                    company_name,
                    payload['initial_admin']['username'],
                    payload['initial_admin']['password']
                )
            except Exception:
                pass

        headers = self.get_success_headers(payload['company'])
        return Response(payload, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        operation_summary="Eliminar empresa",
        operation_description="Elimina usuarios y roles asociados y luego la empresa.",
        responses={
            204: openapi.Response(description="Eliminado"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        },
        tags=["Companies"]
    )
    def destroy(self, request, *args, **kwargs):
        company = self.get_object()
        # Eliminar dependencias directas para evitar restricciones de FK
        User.objects.filter(company=company).delete()
        Role.objects.filter(company=company).delete()
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Actualizar empresa",
        operation_description="Actualiza datos de la empresa. Si cambia el plan, recalcula límites y permisos.",
        request_body=CompanySerializer,
        responses={200: CompanySerializer},
        examples=[
            {
                "name": "Cambiar plan",
                "summary": "Actualizar empresa cambiando el plan",
                "value": {
                    "plan_id": 2
                }
            },
            {
                "name": "Actualizar datos",
                "summary": "Actualizar email y teléfono",
                "value": {
                    "email": "contacto@miempresa.com",
                    "phone": "+1 809-555-0000"
                }
            }
        ],
        tags=["Companies"]
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.get('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        new_plan = serializer.validated_data.get('plan', instance.plan)
        plan_changed = new_plan and instance.plan != new_plan
        company = serializer.save()
        if plan_changed:
            # Recalcular límites
            company.invoice_limit = new_plan.max_invoices
            company.user_limit = new_plan.max_users
            company.role_limit = new_plan.max_roles
            company.clinic_limit = new_plan.max_clinics
            company.save(update_fields=['invoice_limit','user_limit','role_limit','clinic_limit'])
            # Actualizar permisos del rol COMPANY_ADMIN principal
            admin_role = company.roles.filter(role_type='COMPANY_ADMIN').first()
            if admin_role:
                features = new_plan.features or {}
                updated_permissions = {
                    'citas.create': True,
                    'citas.view': True,
                    'users.manage': True,
                    'roles.manage': True
                }
                if features.get('reports'):
                    updated_permissions['reports.view'] = True
                if features.get('api_access'):
                    updated_permissions['api.access'] = True
                admin_role.permissions = updated_permissions
                admin_role.save(update_fields=['permissions'])
        return Response(CompanySerializer(company).data)

    @swagger_auto_schema(
        method='post',
        operation_summary="Resetear cuota",
        operation_description="Resetea el contador de facturas (invoice_count) a 0 para la empresa.",
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING)
        })},
        tags=["Companies"]
    )
    @action(detail=True, methods=['post'])
    def reset_quota(self, request, pk=None):
        company = self.get_object()
        company.invoice_count = 0
        company.save()
        return Response({"detail": "Quota reset"})

class RoleViewSet(viewsets.ModelViewSet):
    """Gestión de roles dentro de una empresa."""
    serializer_class = RoleSerializer
    permission_classes = [IsCompanyAdmin]

    @swagger_auto_schema(
        operation_summary="Listar roles",
        tags=["Roles"],
        responses={
            200: openapi.Response(description="OK"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        }
    )
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Role.objects.none()
        user = self.request.user
        if getattr(user, 'is_super_admin', False):
            return Role.objects.all()
        if getattr(user, 'company_id', None):
            return Role.objects.filter(company_id=user.company_id)
        return Role.objects.none()

    @swagger_auto_schema(
        operation_summary="Crear rol",
        tags=["Roles"],
        request_body=RoleSerializer,
        responses={
            201: RoleSerializer,
            400: openapi.Response(description="Límite de roles excedido"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        },
        examples=[
            {
                "name": "Rol gestor",
                "summary": "Crear rol con permisos específicos",
                "value": {
                    "name": "Gestor",
                    "role_type": "CUSTOM",
                    "permissions": {
                        "invoices.view": True,
                        "invoices.create": True
                    }
                }
            }
        ]
    )
    def perform_create(self, serializer):
        user = self.request.user
        company = getattr(user, 'company', None)
        # Validar límite de roles por plan
        if company:
            try:
                current_roles = Role.objects.filter(company=company).count()
                if company.role_limit > 0 and current_roles >= company.role_limit:
                    raise serializers.ValidationError("Role limit exceeded for this plan")
            except Exception:
                pass
        # Forzar que los Company Admin solo creen roles en su empresa
        if company:
            serializer.save(company=company, is_system=False)
        else:
            # En ausencia de empresa (caso Super Admin), permitir según payload
            serializer.save(is_system=False)

    def perform_update(self, serializer):
        user = self.request.user
        company = getattr(user, 'company', None)
        instance_company = serializer.instance.company
        # Evitar mover roles a otra empresa si es Company Admin
        if company and instance_company and instance_company != company:
            raise serializers.ValidationError({'company_id': 'No puede modificar roles de otra empresa.'})
        serializer.save(is_system=False)
class UserViewSet(viewsets.ModelViewSet):
    """Gestión de usuarios (admin de empresa o super admin)."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Listar usuarios",
        tags=["Users"],
        responses={
            200: openapi.Response(description="OK"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        }
    )
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        user = self.request.user
        if getattr(user, 'is_super_admin', False):
            return User.objects.all()
        if getattr(user, 'company_id', None):
            return User.objects.filter(company_id=user.company_id)
        return User.objects.none()

    @swagger_auto_schema(
        operation_summary="Crear usuario",
        tags=["Users"],
        request_body=UserSerializer,
        responses={
            201: UserSerializer,
            400: openapi.Response(description="Límite de usuarios excedido"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        },
        examples=[
            {
                "name": "Usuario operador",
                "summary": "Crear usuario con rol existente",
                "value": {
                    "username": "operador@miempresa.com",
                    "email": "operador@miempresa.com",
                    "password": "Operador123!",
                    "role_id": 5
                }
            }
        ]
    )
    def perform_create(self, serializer):
        company = self.request.user.company
        if company and company.users.count() >= company.user_limit:
            raise serializers.ValidationError("User limit exceeded for this plan")
        serializer.save(company=company)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(method='get',
        operation_summary="Estadísticas de Dashboard",
        operation_description="Devuelve métricas globales (super admin) o por empresa (admin empresa).",
        responses={200: DashboardStatsSerializer},
        tags=["Dashboard"]
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        if user.is_super_admin:
            # Stats globales
            stats = {
                "total_companies": Company.objects.filter(is_active=True).count(),
                "total_users": User.objects.filter(is_active=True).count(),
            }
        else:
            # Stats de la empresa
            company = user.company
            stats = {
                "users_count": company.users.filter(is_active=True).count(),
                "user_limit": company.user_limit,
            }
        return Response(stats)



    @swagger_auto_schema(method='get',
        operation_summary="Logs de endpoints",
        operation_description="Logs de endpoints API (Super Admin con filtro por empresa opcional, Company Admin ve su empresa).",
        responses={200: openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))},
        tags=["Dashboard"]
    )
    @action(detail=False, methods=['get'])
    def endpoint_logs(self, request):
        from apps.audit.models import EndpointLog
        user = request.user
        if user.is_super_admin:
            queryset = EndpointLog.objects.all()
            company_id = request.query_params.get('company_id')
            if company_id:
                queryset = queryset.filter(company_id=company_id)
        else:
            queryset = EndpointLog.objects.filter(company=user.company)

        # Filtros opcionales
        section = request.query_params.get('section')
        if section:
            queryset = queryset.filter(section=section)

        # Paginación simple
        limit = int(request.query_params.get('limit', 50))
        queryset = queryset.order_by('-created_at')[:limit]

        logs = queryset.values(
            'id', 'user__username', 'company__name', 'section',
            'method', 'path', 'status_code', 'duration_ms', 'created_at'
        )
        return Response(list(logs))



    @swagger_auto_schema(method='get',
        operation_summary="Uso por empresa",
        operation_description="Devuelve métricas por empresa: médicos, pacientes, consultorios, citas y estado del plan. Super Admin puede filtrar ?company_id=UUID.",
        responses={200: openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))},
        tags=["Dashboard"]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin])
    def company_usage(self, request):
        company_id = request.query_params.get('company_id')
        companies = Company.objects.filter(is_active=True)
        if company_id:
            companies = companies.filter(id=company_id)

        data = []
        for company in companies:
            doctors_count = company.doctors.count()
            patients_count = company.patients.count()
            rooms_count = Room.objects.filter(clinic__company=company).count()
            appointments_count = Appointment.objects.filter(patient__company=company).count()

            data.append({
                "company_id": company.id,
                "company_name": company.name,
                "plan_name": getattr(company.plan, 'name', None),
                "doctors": doctors_count,
                "patients": patients_count,
                "rooms": rooms_count,
                "appointments": appointments_count,
            })

        return Response(data)

    @swagger_auto_schema(
        operation_summary="Recaudación mensual por empresa",
        operation_description=(
            "Devuelve, para los últimos 12 meses, la recaudación mensual por empresa en función del precio mensual del plan. "
            "Incluye totales anual por empresa y un resumen global (suma de todas las empresas)."
        ),
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT)},
        tags=["Dashboard"]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin])
    def company_revenue(self, request):
        """
        Retorna la recaudación mensual por empresa basada en pagos reales si existen,
        agrupados por mes (YYYY-MM) para los últimos 12 meses. Si no hay pagos para un
        mes dado, el monto será 0. El nombre del plan se toma del plan actual de la empresa.
        """
        from datetime import datetime

        from ..models.plan_payment import PlanPayment

        company_id = request.query_params.get('company_id')
        companies_qs = Company.objects.filter(is_active=True)
        if company_id:
            companies_qs = companies_qs.filter(id=company_id)

        # Construir últimos 12 meses (label corto y clave YYYY-MM)
        months = []
        today = datetime.now().replace(day=1)
        for i in range(11, -1, -1):
            month_index = today.month - i
            year = today.year
            while month_index <= 0:
                month_index += 12
                year -= 1
            d = datetime(year, month_index, 1)
            months.append({
                'key': d.strftime('%Y-%m'),
                'label': d.strftime('%b').capitalize(),
            })

        # Rango de fechas para filtrar pagos
        start_key = months[0]['key']
        end_key = months[-1]['key']
        start_date = datetime.strptime(start_key + '-01', '%Y-%m-%d').date()
        end_date = datetime.strptime(end_key + '-01', '%Y-%m-%d').date()

        companies_data = []
        summary_by_month = {m['key']: 0.0 for m in months}

        for company in companies_qs:
            plan = getattr(company, 'plan', None)

            # Obtener pagos de la empresa en el rango y agrupar por mes
            payments = (
                PlanPayment.objects
                .filter(company=company, paid_month__gte=start_date, paid_month__lte=end_date)
                .values('paid_month')
                .annotate(total=Sum('amount'))
            )
            payments_map = {p['paid_month'].strftime('%Y-%m'): float(p['total'] or 0) for p in payments}

            monthly_revenue = []
            total_annual = 0.0
            for m in months:
                amount = payments_map.get(m['key'], 0.0)
                monthly_revenue.append({
                    'month': m['label'],
                    'month_date': m['key'],
                    'amount': amount,
                    'plan_name': getattr(plan, 'name', 'Sin plan') if plan else 'Sin plan',
                })
                total_annual += amount
                summary_by_month[m['key']] += amount

            companies_data.append({
                'company_id': str(company.id),
                'company_name': company.name,
                'plan_name': getattr(plan, 'name', 'Sin plan') if plan else 'Sin plan',
                'monthly_revenue': monthly_revenue,
                'total_annual': total_annual,
                'total_monthly_average': (total_annual / 12.0) if months else 0.0,
            })

        # Resumen global
        summary_months = []
        annual_total = 0.0
        for m in months:
            amount = summary_by_month[m['key']]
            annual_total += amount
            summary_months.append({
                'month': m['label'],
                'month_date': m['key'],
                'amount': amount,
            })

        result = {
            'companies': companies_data,
            'summary': {
                'months': summary_months,
                'annual_total': annual_total,
                'monthly_average': (annual_total / 12.0) if months else 0.0,
            }
        }

        return Response(result)


class PlanPaymentViewSet(viewsets.ModelViewSet):
    """Gestión de pagos de planes (solo Super Admin)."""
    queryset = PlanPayment.objects.all()
    serializer_class = PlanPaymentSerializer
    permission_classes = [IsSuperAdmin]

    @swagger_auto_schema(
        operation_summary="Listar pagos",
        operation_description="Lista todos los pagos registrados. Puede filtrar por company_id usando query param.",
        tags=["Plan Payments"],
        responses={
            200: openapi.Response(description="OK"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        company_id = request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        queryset = queryset.order_by('-paid_month', '-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Crear pago",
        operation_description="Registra un nuevo pago mensual para una empresa.",
        request_body=PlanPaymentSerializer,
        tags=["Plan Payments"],
        responses={
            201: PlanPaymentSerializer,
            400: openapi.Response(description="Solicitud inválida"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido")
        },
        examples=[
            {
                "name": "Pago mensual",
                "summary": "Registrar pago de plan de enero 2025",
                "value": {
                    "company": "uuid-empresa",
                    "plan": "plan-id",
                    "paid_month": "2025-01-01",
                    "amount": 300.00,
                    "reference": "PAY-2025-01-001"
                }
            }
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Obtener detalle de pago",
        tags=["Plan Payments"],
        responses={
            200: PlanPaymentSerializer,
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Actualizar pago",
        tags=["Plan Payments"],
        request_body=PlanPaymentSerializer,
        responses={
            200: PlanPaymentSerializer,
            400: openapi.Response(description="Solicitud inválida"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Eliminar pago",
        tags=["Plan Payments"],
        responses={
            204: openapi.Response(description="Eliminado"),
            401: openapi.Response(description="No autenticado"),
            403: openapi.Response(description="Prohibido"),
            404: openapi.Response(description="No encontrado")
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
