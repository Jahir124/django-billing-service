from django.db import models
from core.mixins import AuditDateModel


class Cliente(AuditDateModel):
    identificacion = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Cédula o RUC del cliente. Ej: 0903369387 / 0992988061001",
    )
    razon_social = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    celular = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["razon_social"]

    def __str__(self):
        return f"{self.razon_social} ({self.identificacion})"

    def delete(self, using=None, keep_parents=False):
        """Soft delete: marca is_active=False en lugar de borrar físicamente."""
        self.is_active = False
        self.save(update_fields=["is_active", "modified_at"])
