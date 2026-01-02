from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views.admin import (CompanyViewSet, DashboardViewSet, PlanPaymentViewSet,
                          PlanViewSet, RoleViewSet, UserViewSet)
from .views.views import (CompanySelfView, CookieTokenRefreshView,
                          CurrentUserAPIView, LogoutView, PublicPlansAPIView,
                          RegisterAPIView, TokenObtainPairWithUserView,
                          UserSelfView)

router = DefaultRouter()
router.register('companies', CompanyViewSet, basename='company')
router.register('users', UserViewSet, basename='user')
router.register('roles', RoleViewSet, basename='role')
router.register('plans', PlanViewSet, basename='plan')
router.register('plan-payments', PlanPaymentViewSet, basename='plan-payment')
router.register('dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    # Rutas específicas primero para evitar colisión con router 'users/<pk>/'
    path("company/me/", CompanySelfView.as_view(), name="api-company-self"),
    path("users/me/", UserSelfView.as_view(), name="api-user-self"),
    path("register/", RegisterAPIView.as_view(), name="api-register"),
    path("user/", CurrentUserAPIView.as_view(), name="api-current-user"),
    path("jwt/", TokenObtainPairWithUserView.as_view(), name="token_obtain_pair_email"),
    path("jwt/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh_cookie"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    # Público: planes activos (para landing)
    path("public/plans/", PublicPlansAPIView.as_view(), name="public-plans"),
    # Router genérico al final
    path('', include(router.urls)),
]
