import pytest
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.lineas.models import EstadoLinea
from apps.cobranza.models import EstadoRubro, CollectionsRequestLog, LogStatus, ActionTaken
from .factories import ClienteFactory, LineaServicioFactory, RubroFactory


@pytest.mark.django_db
class TestProcesoControlMorosidad:
    """Tests de la lógica de la tarea de cobranza"""

    def _run_task(self):
        """Ejecuta la tarea de forma síncrona sin Celery"""
        from apps.cobranza.tasks import proceso_control_morosidad
        proceso_control_morosidad()

    def test_suspende_linea_con_rubros_vencidos(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.ACTIVO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=1),
            valor_total=Decimal("50.00"),
        )
        self._run_task()
        linea.refresh_from_db()
        assert linea.estado_linea == EstadoLinea.SUSPENDIDO
        assert linea.saldo_vencido == Decimal("50.00")

    def test_reactiva_linea_sin_deuda(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.SUSPENDIDO)
        self._run_task()
        linea.refresh_from_db()
        assert linea.estado_linea == EstadoLinea.ACTIVO
        assert linea.saldo_vencido == 0

    def test_idempotente_doble_ejecucion(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.ACTIVO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=1),
            valor_total=Decimal("30.00"),
        )
        self._run_task()
        self._run_task()
        linea.refresh_from_db()
        assert linea.estado_linea == EstadoLinea.SUSPENDIDO
        logs = CollectionsRequestLog.objects.filter(linea_servicio=linea)
        assert logs.count() == 2  

    def test_no_suspende_linea_cancelada(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.CANCELADO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=1),
        )
        self._run_task()
        linea.refresh_from_db()
        assert linea.estado_linea == EstadoLinea.CANCELADO

    def test_no_suspende_linea_no_instalada(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.NO_INSTALADO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=1),
        )
        self._run_task()
        linea.refresh_from_db()
        assert linea.estado_linea == EstadoLinea.NO_INSTALADO

    def test_genera_log_success(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.ACTIVO)
        self._run_task()
        log = CollectionsRequestLog.objects.get(linea_servicio=linea)
        assert log.status == LogStatus.SUCCESS
        assert log.finished_at is not None

    def test_log_action_suspend(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.ACTIVO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=1),
        )
        self._run_task()
        log = CollectionsRequestLog.objects.get(linea_servicio=linea)
        assert log.action_taken == ActionTaken.SUSPEND

    def test_log_action_unsuspend(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.SUSPENDIDO)
        self._run_task()
        log = CollectionsRequestLog.objects.get(linea_servicio=linea)
        assert log.action_taken == ActionTaken.UNSUSPEND

    def test_rubros_no_vencidos_no_cuentan(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.ACTIVO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() + timedelta(days=10),
        )
        self._run_task()
        linea.refresh_from_db()
        assert linea.estado_linea == EstadoLinea.ACTIVO

    def test_saldo_acumula_multiples_rubros(self):
        linea = LineaServicioFactory(estado_linea=EstadoLinea.ACTIVO)
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=1),
            valor_total=Decimal("25.00"),
        )
        RubroFactory(
            linea_servicio=linea,
            estado_rubro=EstadoRubro.NO_PAGADO,
            fecha_vencimiento=timezone.now() - timedelta(days=2),
            valor_total=Decimal("75.00"),
        )
        self._run_task()
        linea.refresh_from_db()
        assert linea.saldo_vencido == Decimal("100.00")
