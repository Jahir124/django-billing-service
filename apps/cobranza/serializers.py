from rest_framework import serializers
from .models import Rubro, CollectionsRequestLog


class RubroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rubro
        fields = [
            "id",
            "linea_servicio",
            "valor_total",
            "estado_rubro",
            "fecha_emision",
            "fecha_vencimiento",
            "fecha_pago",
            "created_at",
            "modified_at",
        ]
        read_only_fields = ["id", "created_at", "modified_at"]

    def validate(self, attrs):
        fe = attrs.get("fecha_emision")
        fv = attrs.get("fecha_vencimiento")
        if fe and fv and fv <= fe:
            raise serializers.ValidationError(
                {"fecha_vencimiento": "Debe ser posterior a la fecha de emisión."}
            )
        return attrs


class CollectionsRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionsRequestLog
        fields = [
            "id",
            "linea_servicio",
            "started_at",
            "finished_at",
            "status",
            "unpaid_count",
            "action_taken",
            "error_message",
        ]
        read_only_fields = fields
