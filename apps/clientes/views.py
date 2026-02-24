from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Cliente
from .serializers import ClienteSerializer
from .filters import ClienteFilter


class ClienteViewSet(viewsets.ModelViewSet):
    """
    CRUD de Clientes con soft delete.

    - Solo admin puede hacer DELETE (eliminación lógica).
    - El resto de operaciones requieren autenticación.
    """

    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filterset_class = ClienteFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["identificacion", "razon_social", "email"]
    ordering_fields = ["razon_social", "created_at"]
    ordering = ["razon_social"]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        """Soft delete: cambia is_active=False."""
        instance = self.get_object()
        if not instance.is_active:
            return Response(
                {"detail": "El cliente ya se encuentra eliminado."},
                status=status.HTTP_409_CONFLICT,
            )
        instance.delete()
        return Response(
            {"detail": "Cliente eliminado lógicamente."},
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
