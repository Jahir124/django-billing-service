from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import IntegrityError

from .models import LineaServicio
from .serializers import LineaServicioSerializer
from .filters import LineaServicioFilter


class LineaServicioViewSet(viewsets.ModelViewSet):
    """ CRUD de Líneas de Servicio"""

    queryset = LineaServicio.objects.select_related("cliente").all()
    serializer_class = LineaServicioSerializer
    filterset_class = LineaServicioFilter

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "Ya existe una línea con ese número para este cliente."},
                status=status.HTTP_409_CONFLICT,
            )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        try:
            return super().update(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "Ya existe una línea con ese número para este cliente."},
                status=status.HTTP_409_CONFLICT,
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_active:
            return Response(
                {"detail": "La línea ya se encuentra eliminada."},
                status=status.HTTP_409_CONFLICT,
            )
        instance.delete()
        return Response(
            {"detail": "Línea eliminada lógicamente."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="estado-cobranza")
    def estado_cobranza(self, request, pk=None):
        """Resumen de cobranza de la línea"""
        from apps.cobranza.models import Rubro, CollectionsRequestLog, EstadoRubro
        from apps.cobranza.serializers import CollectionsRequestLogSerializer
        from django.utils import timezone

        linea = self.get_object()

        unpaid_count = Rubro.objects.filter(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento__lt=timezone.now(),
        ).count()

        logs = CollectionsRequestLog.objects.filter(linea_servicio=linea).order_by(
            "-started_at"
        )[:10]

        return Response(
            {
                "linea_id": linea.id,
                "linea_numero": linea.linea_numero,
                "estado_linea": linea.estado_linea,
                "saldo_vencido": str(linea.saldo_vencido),
                "unpaid_count": unpaid_count,
                "ultimos_logs": CollectionsRequestLogSerializer(logs, many=True).data,
            }
        )
