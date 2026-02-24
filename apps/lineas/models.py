from django.db import models
from django.core.exceptions import ValidationError
from core.mixins import AuditDateModel
from apps.clientes.models import Cliente


class EstadoLinea(models.TextChoices):
    NO_INSTALADO = "NO_INSTALADO", "No Instalado"
    ACTIVO = "ACTIVO", "Activo"
    SUSPENDIDO = "SUSPENDIDO", "Suspendido"
    CANCELADO = "CANCELADO", "Cancelado"

ESTADOS_NO_GESTIONABLES = {EstadoLinea.NO_INSTALADO, EstadoLinea.CANCELADO}


class LineaServicio(AuditDateModel):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="lineas",
    )
    linea_numero = models.PositiveSmallIntegerField(
        help_text="Número de línea del cliente (>=1). Único por cliente."
    )
    estado_linea = models.CharField(
        max_length=20,
        choices=EstadoLinea.choices,
        default=EstadoLinea.NO_INSTALADO,
    )
    fecha_instalacion = models.DateField(blank=True, null=True)
    saldo_vencido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Calculado automáticamente por la tarea de cobranza.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Línea de Servicio"
        verbose_name_plural = "Líneas de Servicio"
        unique_together = ("cliente", "linea_numero")
        ordering = ["cliente", "linea_numero"]

    def __str__(self):
        return f"Línea {self.linea_numero} – {self.cliente.razon_social} [{self.estado_linea}]"

    def clean(self):
        if self.linea_numero is not None and self.linea_numero < 1:
            raise ValidationError({"linea_numero": "El número de línea debe ser >= 1."})

        if self.estado_linea == EstadoLinea.ACTIVO and self.cliente_id:
            try:
                cliente = Cliente.objects.get(pk=self.cliente_id)
                if not cliente.is_active:
                    raise ValidationError(
                        {
                            "estado_linea": (
                                "No se puede activar una línea de un cliente inactivo."
                            )
                        }
                    )
            except Cliente.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.is_active = False
        self.save(update_fields=["is_active", "modified_at"])
