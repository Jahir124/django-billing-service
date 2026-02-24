from rest_framework import serializers
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id",
            "identificacion",
            "razon_social",
            "email",
            "celular",
            "is_active",
            "created_at",
            "modified_at",
        ]
        read_only_fields = ["id", "created_at", "modified_at"]

    def validate_identificacion(self, value):
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError(
                "La identificación debe contener solo dígitos."
            )
        if len(value) not in (10, 13):
            raise serializers.ValidationError(
                "La identificación debe tener 10 dígitos (cédula) o 13 (RUC)."
            )
        return value
