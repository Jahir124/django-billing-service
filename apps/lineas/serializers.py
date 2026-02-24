from rest_framework import serializers
from django.db import IntegrityError
from .models import LineaServicio, EstadoLinea
from apps.clientes.models import Cliente


class LineaServicioSerializer(serializers.ModelSerializer):
    cliente_razon_social = serializers.CharField(
        source="cliente.razon_social", read_only=True
    )

    class Meta:
        model = LineaServicio
        fields = [
            "id",
            "cliente",
            "cliente_razon_social",
            "linea_numero",
            "estado_linea",
            "fecha_instalacion",
            "saldo_vencido",
            "is_active",
            "created_at",
            "modified_at",
        ]
        read_only_fields = ["id", "saldo_vencido", "created_at", "modified_at"]

    def validate_linea_numero(self, value):
        if value < 1:
            raise serializers.ValidationError("El número de línea debe ser >= 1.")
        return value

    def validate(self, attrs):
        cliente = attrs.get("cliente") or (
            self.instance.cliente if self.instance else None
        )
        estado = attrs.get("estado_linea") or (
            self.instance.estado_linea if self.instance else EstadoLinea.NO_INSTALADO
        )

        if estado == EstadoLinea.ACTIVO and cliente and not cliente.is_active:
            raise serializers.ValidationError(
                {"estado_linea": "No se puede activar una línea de un cliente inactivo."}
            )
        return attrs

    def validate_cliente(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "No se puede asociar una línea a un cliente inactivo."
            )
        return value
