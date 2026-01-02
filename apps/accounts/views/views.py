import io

from apps.s3.s3_services import (S3ConfigError, generate_presigned_url,
                                 get_company_bucket_name, upload_file)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from ..models.company import Company
from ..models.plan import Plan
from ..permissions import IsCompanyAdmin
from ..serializers.admin import CompanySerializer, PlanSerializer
from ..serializers.admin import UserSerializer as UserWithDetailsSerializer
from ..serializers.serializers import (RegisterSerializer,
                                       TokenObtainPairWithUserSerializer,
                                       UserSerializer)

User = get_user_model()


class PublicPlansAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True).order_by('price_monthly')
        data = PlanSerializer(plans, many=True).data
        return Response(data)


class CurrentUserAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserWithDetailsSerializer(request.user).data)

class ObtainAuthTokenByEmail(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"detail": "email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserWithDetailsSerializer(user).data
        return Response({"token": token.key, "user": user_data})


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"id": user.pk, "username": user.username, "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class TokenObtainPairWithUserView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = TokenObtainPairWithUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        access = data.get("access")
        refresh = data.get("refresh")
        user = data.get("user")

         # Serializar el usuario con el serializer completo que incluye role/company/plan
        user_obj = User.objects.filter(username=user.get('username')).select_related(
            'role', 'company', 'company__plan'
        ).first()

        user_data = UserWithDetailsSerializer(user_obj).data if user_obj else user

        resp = Response(
            {"access": access, "user": user_data},
            status=status.HTTP_200_OK,
        )
        # Setear cookie HttpOnly para refresh (solo backend puede leerla)
        # En producción usar secure=True y ajustar samesite según tu dominio
        resp.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=False,  # poner True en producción (HTTPS)
            samesite="Lax",
            path="/api/auth/jwt/refresh/"
        )
        return resp




class CookieTokenRefreshView(APIView):
    """
    Lee refresh token desde cookie HttpOnly 'refresh_token',
    valida, rota y devuelve nuevo access; setea nueva cookie para refresh.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.COOKIES.get("refresh_token")
        if not token:
            return Response({"detail": "No refresh token cookie"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            # valida el refresh actual
            old_refresh = RefreshToken(token)
            user_id = old_refresh.get("user_id")
            # crear nuevo refresh (rotación)
            new_refresh = RefreshToken.for_user(get_object_or_404(User, pk=user_id))
            access = str(new_refresh.access_token)
            # marcar el refresh antiguo como blacklisted si está habilitado
            try:
                old_refresh.blacklist()
            except Exception:
                pass
            resp = Response({"access": access}, status=status.HTTP_200_OK)
            resp.set_cookie(
                key="refresh_token",
                value=str(new_refresh),
                httponly=True,
                secure=False,     # en desarrollo false; en producción True
                samesite="Lax",
                path="/api/auth/jwt/refresh/"
            )
            return resp
        except TokenError:
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    Borra la cookie de refresh y blacklistea el refresh token si existe.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # nombre de cookie que usa tu backend para el refresh (ajusta si es distinto)
        cookie_name = getattr(settings, "SIMPLE_JWT_REFRESH_COOKIE_NAME", "refresh_token")
        response = Response({"detail": "logged out"}, status=status.HTTP_200_OK)
        # eliminar cookie (incluir mismo path/domain si corresponde)
        response.delete_cookie(cookie_name, path='/', domain=getattr(settings, 'SESSION_COOKIE_DOMAIN', None))
        response.delete_cookie('_MEDICAL_DATA_AUTH_SESSION_KEY_', path='/', domain=getattr(settings, 'SESSION_COOKIE_DOMAIN', None))
        return response


class CompanySelfView(APIView):
    """Permite a COMPANY_ADMIN ver/editar los datos de su empresa y subir logo."""
    permission_classes = [permissions.IsAuthenticated, IsCompanyAdmin]

    def get(self, request):
        company = request.user.company
        if not company:
            return Response({"detail": "No company associated"}, status=400)
        return Response(CompanySerializer(company).data)

    def put(self, request):
        company = request.user.company
        if not company:
            return Response({"detail": "No company associated"}, status=400)
        data = request.data.copy()
        # Manejar archivo de logo si se envía
        logo_file = request.FILES.get('logo')
        if logo_file:
            # Validaciones: tipo y tamaño (<= 1 MB)
            allowed_types = {"image/png", "image/jpeg"}
            max_size = 1 * 1024 * 1024
            if getattr(logo_file, 'size', 0) > max_size:
                return Response({"detail": "El logo excede 1MB"}, status=400)
            if getattr(logo_file, 'content_type', '') not in allowed_types:
                return Response({"detail": "Formato de logo inválido. Solo PNG o JPG"}, status=400)
            bucket = get_company_bucket_name(company.rnc)
            # Guardar siempre bajo una ruta estable en carpeta 'img/'
            ext = '.png'
            ct = getattr(logo_file, 'content_type', '')
            if ct == 'image/jpeg':
                ext = '.jpg'
            key = f"img/logo{ext}"
            try:
                upload_file(logo_file, bucket, key)
            except S3ConfigError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            company.logo.name = key
            company.save(update_fields=["logo"])
        serializer = CompanySerializer(company, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserSelfView(APIView):
    """Permite a cualquier usuario editar su propio perfil. Avatar solo para COMPANY_ADMIN."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserWithDetailsSerializer(request.user).data)

    def put(self, request):
        user = request.user
        data = request.data.copy()
        # Controlar subida de avatar solo para COMPANY_ADMIN
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            if not getattr(user, 'is_company_admin', False):
                return Response({"detail": "Avatar upload not allowed for this role"}, status=403)
            # Validaciones: tipo y tamaño (<= 1 MB)
            allowed_types = {"image/png", "image/jpeg"}
            max_size = 1 * 1024 * 1024
            if getattr(avatar_file, 'size', 0) > max_size:
                return Response({"detail": "El avatar excede 1MB"}, status=400)
            if getattr(avatar_file, 'content_type', '') not in allowed_types:
                return Response({"detail": "Formato de avatar inválido. Solo PNG o JPG"}, status=400)
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            key = f"users/{user.id}/avatar/{avatar_file.name}"
            try:
                upload_file(avatar_file, bucket, key)
            except S3ConfigError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            user.avatar.name = key
            user.save(update_fields=["avatar"])
        # Permitir actualizar first_name, last_name, email, password
        allowed_fields = {"first_name", "last_name", "email", "password"}
        filtered = {k: v for k, v in data.items() if k in allowed_fields}
        # Si no hay más campos, devolver perfil
        if not filtered and not avatar_file:
            return Response(UserWithDetailsSerializer(user).data)
        # Aplicar cambios
        if filtered.get("password"):
            user.set_password(filtered.pop("password"))
        for k, v in filtered.items():
            setattr(user, k, v)
        user.save()
        return Response(UserWithDetailsSerializer(user).data)
