from rest_framework.routers import DefaultRouter
from .views import LineaServicioViewSet

router = DefaultRouter()
router.register(r"lineas", LineaServicioViewSet, basename="linea")

urlpatterns = router.urls
