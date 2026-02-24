from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Rubro, CollectionsRequestLog
from .serializers import RubroSerializer, CollectionsRequestLogSerializer
from .tasks import proceso_control_morosidad


class RubroViewSet(viewsets.ModelViewSet):
    """CRUD de Rubros"""

    queryset = Rubro.objects.select_related("linea_servicio").all()
    serializer_class = RubroSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="ejecutar-cobranza",
            permission_classes=[IsAdminUser])
    def ejecutar_cobranza(self, request):
        """Dispara manualmente el proceso de control de morosidad"""
        task = proceso_control_morosidad.delay()
        return Response(
            {"detail": "Tarea encolada.", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED,
        )


class CollectionsRequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Logs de ejecución del proceso de cobranza"""

    queryset = CollectionsRequestLog.objects.select_related("linea_servicio").all()
    serializer_class = CollectionsRequestLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["linea_servicio", "status", "action_taken"]
