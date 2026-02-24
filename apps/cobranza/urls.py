from rest_framework.routers import DefaultRouter
from .views import RubroViewSet, CollectionsRequestLogViewSet

router = DefaultRouter()
router.register(r"rubros", RubroViewSet, basename="rubro")
router.register(r"cobranza-logs", CollectionsRequestLogViewSet, basename="cobranza-log")

urlpatterns = router.urls
