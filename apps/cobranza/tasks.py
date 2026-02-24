import logging
from celery import shared_task
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="cobranza.proceso_control_morosidad",
)
def proceso_control_morosidad(self):
    """ Tarea periódica (cada 5 min) que evalúa el estado de morosidad de todas las líneas activas y actualiza su estado"""
    from apps.lineas.models import LineaServicio, EstadoLinea, ESTADOS_NO_GESTIONABLES
    from apps.cobranza.models import (
        Rubro,
        EstadoRubro,
        CollectionsRequestLog,
        LogStatus,
        ActionTaken,
    )

    now = timezone.now()
    logger.info("[COBRANZA] Inicio de proceso. Timestamp: %s", now)

    lineas = (
        LineaServicio.objects.select_related("cliente")
        .filter(is_active=True)
        .exclude(estado_linea__in=list(ESTADOS_NO_GESTIONABLES))
    )

    total = lineas.count()
    logger.info("[COBRANZA] Líneas a procesar: %d", total)

    for linea in lineas:
        log = CollectionsRequestLog(
            linea_servicio=linea,
            started_at=now,
            status=LogStatus.SUCCESS,
        )

        try:
            with transaction.atomic():
                rubros_vencidos = Rubro.objects.filter(
                    linea_servicio=linea,
                    estado_rubro=EstadoRubro.NO_PAGADO,
                    fecha_vencimiento__lt=now,
                )

                unpaid_count = rubros_vencidos.count()
                saldo = rubros_vencidos.aggregate(total=Sum("valor_total"))["total"] or 0

                log.unpaid_count = unpaid_count

                linea.saldo_vencido = saldo

                action = ActionTaken.NONE

                if unpaid_count > 0:
                    if linea.estado_linea != EstadoLinea.SUSPENDIDO:
                        LineaServicio.objects.filter(pk=linea.pk).update(
                            estado_linea=EstadoLinea.SUSPENDIDO,
                            saldo_vencido=saldo,
                            modified_at=now,
                        )
                        action = ActionTaken.SUSPEND
                        logger.info(
                            "[COBRANZA] Línea %d SUSPENDIDA. Rubros vencidos: %d | Saldo: %s",
                            linea.pk, unpaid_count, saldo,
                        )
                    else:
                        LineaServicio.objects.filter(pk=linea.pk).update(
                            saldo_vencido=saldo,
                            modified_at=now,
                        )
                        logger.debug(
                            "[COBRANZA] Línea %d ya suspendida. Saldo actualizado: %s",
                            linea.pk, saldo,
                        )
                else:
                    if linea.estado_linea == EstadoLinea.SUSPENDIDO:
                        LineaServicio.objects.filter(pk=linea.pk).update(
                            estado_linea=EstadoLinea.ACTIVO,
                            saldo_vencido=0,
                            modified_at=now,
                        )
                        action = ActionTaken.UNSUSPEND
                        logger.info(
                            "[COBRANZA] Línea %d REACTIVADA. Sin deuda pendiente.",
                            linea.pk,
                        )
                    else:
                        LineaServicio.objects.filter(pk=linea.pk).update(
                            saldo_vencido=0,
                            modified_at=now,
                        )

                log.action_taken = action
                log.finished_at = timezone.now()
                log.status = LogStatus.SUCCESS
                log.save()

        except Exception as exc:
            logger.exception(
                "[COBRANZA] Error procesando línea %d: %s", linea.pk, exc
            )
            log.status = LogStatus.FAILED
            log.error_message = str(exc)
            log.finished_at = timezone.now()
            log.save()

    logger.info("[COBRANZA] Proceso finalizado. Total procesadas: %d", total)
    return {"processed": total, "timestamp": str(now)}
