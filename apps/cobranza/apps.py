from django.apps import AppConfig


class CobranzaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cobranza"
    verbose_name = "Cobranza"

    def ready(self):
        """Registra la tarea periódica en Celery Beat al arrancar"""
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            import json

            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=5,
                period=IntervalSchedule.MINUTES,
            )

            PeriodicTask.objects.update_or_create(
                name="Proceso Control Morosidad (cada 5 min)",
                defaults={
                    "interval": schedule,
                    "task": "cobranza.proceso_control_morosidad",
                    "args": json.dumps([]),
                    "enabled": True,
                },
            )
        except Exception:
            pass
