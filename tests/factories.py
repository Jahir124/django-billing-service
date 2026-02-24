import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta

from apps.clientes.models import Cliente
from apps.lineas.models import LineaServicio, EstadoLinea
from apps.cobranza.models import Rubro, EstadoRubro


class ClienteFactory(DjangoModelFactory):
    class Meta:
        model = Cliente

    identificacion = factory.Sequence(lambda n: f"{1000000000 + n}")
    razon_social = factory.Sequence(lambda n: f"Empresa {n} S.A.")
    email = factory.LazyAttribute(lambda o: f"{o.razon_social.lower().replace(' ', '')}@test.com")
    celular = "0991234567"
    is_active = True


class LineaServicioFactory(DjangoModelFactory):
    class Meta:
        model = LineaServicio
        exclude = ["_skip_clean"]

    cliente = factory.SubFactory(ClienteFactory)
    linea_numero = factory.Sequence(lambda n: n + 1)
    estado_linea = EstadoLinea.ACTIVO
    is_active = True


class RubroFactory(DjangoModelFactory):
    class Meta:
        model = Rubro
        exclude = ["_skip_clean"]

    linea_servicio = factory.SubFactory(LineaServicioFactory)
    valor_total = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    estado_rubro = EstadoRubro.NO_PAGADO
    fecha_emision = factory.LazyFunction(lambda: timezone.now() - timedelta(days=30))
    fecha_vencimiento = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))
