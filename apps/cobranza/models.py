from django.db import models
from django.core.exceptions import ValidationError
from core.mixins import AuditDateModel
from apps.lineas.models import LineaServicio


class EstadoRubro(models.TextChoices):
    NO_PAGADO = "NO_PAGADO", "No Pagado"
    PAGADO = "PAGADO", "Pagado"
    VENCIDO = "VENCIDO", "Vencido"
    ANULADO = "ANULADO", "Anulado"


class Rubro(AuditDateModel):
    linea_servicio = models.ForeignKey( 
        LineaServicio,
        on_delete=models.PROTECT,
        related_name="rubros",
    )
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    estado_rubro = models.CharField(
        max_length=20,
        choices=EstadoRubro.choices,
        default=EstadoRubro.NO_PAGADO,
    )
    fecha_emision = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField() 
    fecha_pago = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Rubro"
        verbose_name_plural = "Rubros"
        ordering = ["-fecha_vencimiento"]

    def __str__(self):
        return (
            f"Rubro {self.id} – Línea {self.linea_servicio_id} "
            f"| ${self.valor_total} [{self.estado_rubro}]"
        )

    def clean(self):
        if self.valor_total is not None and self.valor_total <= 0:
            raise ValidationError({"valor_total": "El valor del rubro debe ser mayor a 0."})
        if (
            self.fecha_vencimiento
            and self.fecha_emision
            and self.fecha_vencimiento <= self.fecha_emision
        ):
            raise ValidationError(
                {"fecha_vencimiento": "La fecha de vencimiento debe ser posterior a la emisión."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class LogStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "Exitoso"
    FAILED = "FAILED", "Fallido"


class ActionTaken(models.TextChoices):
    NONE = "NONE", "Sin acción"
    SUSPEND = "SUSPEND", "Suspendido"
    UNSUSPEND = "UNSUSPEND", "Reactivado"


class CollectionsRequestLog(models.Model):
    """Registro de cada ejecución del proceso de cobranza por línea"""

    linea_servicio = models.ForeignKey(
        LineaServicio,
        on_delete=models.CASCADE,
        related_name="collection_logs",
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=LogStatus.choices,
        default=LogStatus.SUCCESS,
    )
    unpaid_count = models.PositiveSmallIntegerField(default=0)
    action_taken = models.CharField(
        max_length=20,
        choices=ActionTaken.choices,
        default=ActionTaken.NONE,
        blank=True,
    )
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Log de Cobranza"
        verbose_name_plural = "Logs de Cobranza"
        ordering = ["-started_at"]

    def __str__(self):
        return (
            f"Log Línea {self.linea_servicio_id} "
            f"| {self.started_at:%Y-%m-%d %H:%M} | {self.status}"
        )
