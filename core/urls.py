from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView
try:
    from drf_spectacular.views import SpectacularSwaggerUIView
except ImportError:
    from drf_spectacular.views import SpectacularSwaggerView as SpectacularSwaggerUIView

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT Auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API endpoints
    path("api/", include("apps.clientes.urls")),
    path("api/", include("apps.lineas.urls")),
    path("api/", include("apps.cobranza.urls")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerUIView.as_view(url_name="schema"), name="swagger-ui"),

    # Healthcheck
    path("health/", include("core.health")),
]
