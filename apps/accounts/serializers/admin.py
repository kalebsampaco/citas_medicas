from apps.s3.s3_services import generate_presigned_url, get_company_bucket_name
from django.conf import settings
from rest_framework import serializers

from ..models.company import Company
from ..models.plan import Plan
from ..models.plan_payment import PlanPayment
from ..models.role import Role
from ..models.user import User

# Evitar import circular: representar company como clave primaria read-only


class PlanSerializer(serializers.ModelSerializer):
    # Documentar tipo de plan
    plan_type = serializers.ChoiceField(choices=[
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ])
    # Ayuda en límites y features
    max_invoices = serializers.IntegerField(help_text="Máximo de facturas permitidas por periodo")
    max_users = serializers.IntegerField(help_text="Máximo de usuarios activos permitidos")
    max_roles = serializers.IntegerField(help_text="Máximo de roles configurables")
    max_clinics = serializers.IntegerField(help_text="Máximo de clínicas permitidas")
    features = serializers.DictField(help_text="Flags del plan", required=False, default=dict)

    class Meta:
        model = Plan
        fields = [
            'id','name','plan_type',
            'max_invoices','max_users','max_roles','max_clinics',
            'price_monthly', 'is_active',
            'features'
        ]

class RoleSerializer(serializers.ModelSerializer):
    # Choices completos permitidos para roles de empresa (excluye SUPER_ADMIN)
    role_type = serializers.ChoiceField(choices=[
        ('COMPANY_ADMIN', 'Administrador de Empresa'),
        ('ACCOUNTANT', 'Contador'),
        ('VIEWER', 'Visualizador'),
        ('CUSTOM', 'Rol Personalizado')
    ], required=True)
    company = serializers.PrimaryKeyRelatedField(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True,
        required=True
    )
    class Meta:
        model = Role
        fields = ['id','name','role_type','permissions','is_system','company','company_id']
        read_only_fields = ['is_system','company']

    def validate(self, attrs):
        # Evitar que se cree un rol de sistema desde empresa
        if attrs.get('role_type') == 'SUPER_ADMIN':
            raise serializers.ValidationError({'role_type': 'SUPER_ADMIN no está permitido.'})
        return attrs

class CompanySerializer(serializers.ModelSerializer):
    # Documentar ambiente DGII
    dgii_ambiente_default = serializers.ChoiceField(choices=[
        ('PROD', 'Producción'),
        ('TEST', 'Pruebas')
    ], required=False)
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(),
        source='plan',
        write_only=True,
        required=False
    )
    # Campos calculados: eliminar source redundante (ya coincide con el nombre)
    invoices_remaining = serializers.IntegerField(read_only=True)
    is_near_limit = serializers.BooleanField(read_only=True)
    is_over_limit = serializers.BooleanField(read_only=True)

    # Campos de clínicas
    clinics_count = serializers.IntegerField(read_only=True)
    clinics_remaining = serializers.IntegerField(read_only=True)
    is_clinics_over_limit = serializers.BooleanField(read_only=True)
    is_payment_active = serializers.BooleanField(read_only=True)

    logo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = [
            'id','name','rnc','email','phone','address',
            'dgii_certificate_uploaded','dgii_ambiente_default',
            'invoice_count','invoice_limit','invoices_remaining',
            'is_near_limit','is_over_limit',
            'user_limit','role_limit',
            'clinic_limit','clinics_count','clinics_remaining','is_clinics_over_limit',
            'is_payment_active',
            'plan','plan_id',
            'logo_url'
        ]
        # Marcar límites como solo lectura: se derivan del plan seleccionado
        read_only_fields = [
            'invoice_count', 'invoices_remaining', 'is_near_limit', 'is_over_limit',
            'invoice_limit', 'user_limit', 'role_limit',
            'clinic_limit', 'clinics_count', 'clinics_remaining', 'is_clinics_over_limit',
            'is_payment_active'
        ]

    def get_logo_url(self, obj: Company):
        try:
            if obj.logo and obj.logo.name:
                bucket = get_company_bucket_name(obj.rnc)
                return generate_presigned_url(bucket, obj.logo.name, expires=3600)
        except Exception:
            pass
        return None

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True,
        required=False
    )
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True,
        required=False
    )
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id','username','email','password',
            'role','role_id','company','company_id',
            'is_active','avatar_url'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def get_avatar_url(self, obj: User):
        try:
            if obj.avatar and obj.avatar.name:
                return generate_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, obj.avatar.name, expires=3600)
        except Exception:
            pass
        return None

class DashboardStatsSerializer(serializers.Serializer):
    # Stats super admin
    total_users = serializers.IntegerField(required=False)
    total_companies = serializers.IntegerField(required=False)
    total_invoices = serializers.IntegerField(required=False)
    invoices_success = serializers.IntegerField(required=False)
    invoices_error = serializers.IntegerField(required=False)
    companies_near_limit = serializers.IntegerField(required=False)
    top_errors = serializers.ListField(child=serializers.DictField(), required=False)

    # Stats company admin
    invoice_count = serializers.IntegerField(required=False)
    invoice_limit = serializers.IntegerField(required=False)
    invoices_remaining = serializers.IntegerField(required=False)
    is_near_limit = serializers.BooleanField(required=False)
    users_count = serializers.IntegerField(required=False)
    user_limit = serializers.IntegerField(required=False)


class InitialAdminSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField()


class CompanyCreateResponseSerializer(serializers.Serializer):
    company = CompanySerializer()
    initial_admin = InitialAdminSerializer()


class PlanPaymentSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), required=False, allow_null=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    paid_month = serializers.CharField(help_text="Formato YYYY-MM (se convierte a primer día del mes)")

    class Meta:
        model = PlanPayment
        fields = ['id', 'company', 'company_name', 'plan', 'plan_name', 'paid_month', 'amount', 'reference', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_paid_month(self, value):
        """Convierte YYYY-MM a YYYY-MM-01 (primer día del mes)."""
        from datetime import datetime
        try:
            # Si viene en formato YYYY-MM, agregar -01
            if len(value) == 7 and value[4] == '-':
                value = value + '-01'
            # Validar que sea una fecha válida
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            raise serializers.ValidationError("Formato de fecha inválido. Use YYYY-MM o YYYY-MM-DD.")

    def create(self, validated_data):
        from datetime import datetime
        paid_month_str = validated_data.get('paid_month')
        # Asegurar formato YYYY-MM-DD
        if len(paid_month_str) == 7:
            paid_month_str = paid_month_str + '-01'
        validated_data['paid_month'] = datetime.strptime(paid_month_str, '%Y-%m-%d').date()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from datetime import datetime
        paid_month_str = validated_data.get('paid_month', instance.paid_month.strftime('%Y-%m-%d'))
        # Asegurar formato YYYY-MM-DD
        if isinstance(paid_month_str, str) and len(paid_month_str) == 7:
            paid_month_str = paid_month_str + '-01'
        if isinstance(paid_month_str, str):
            validated_data['paid_month'] = datetime.strptime(paid_month_str, '%Y-%m-%d').date()
        return super().update(instance, validated_data)
