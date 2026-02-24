import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.lineas.models import LineaServicio, EstadoLinea
from apps.clientes.models import Cliente
from .factories import ClienteFactory, LineaServicioFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_user(db):
    user = User.objects.create_user("u", "u@t.com", "pass")
    return user


@pytest.fixture
def auth_client(api_client, auth_user):
    api_client.force_authenticate(user=auth_user)
    return api_client


@pytest.mark.django_db
class TestLineaServicio:
    def test_create_linea(self, auth_client):
        cliente = ClienteFactory()
        url = reverse("linea-list")
        data = {
            "cliente": cliente.pk,
            "linea_numero": 1,
            "estado_linea": EstadoLinea.ACTIVO,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_unique_together_cliente_linea_numero(self, auth_client):
        linea = LineaServicioFactory()
        url = reverse("linea-list")
        data = {
            "cliente": linea.cliente.pk,
            "linea_numero": linea.linea_numero,
            "estado_linea": EstadoLinea.ACTIVO,
        }
        response = auth_client.post(url, data)
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
        )

    def test_no_activar_linea_cliente_inactivo(self, auth_client):
        cliente = ClienteFactory(is_active=False)
        url = reverse("linea-list")
        data = {
            "cliente": cliente.pk,
            "linea_numero": 1,
            "estado_linea": EstadoLinea.ACTIVO,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_linea_numero_menor_a_1(self, auth_client):
        cliente = ClienteFactory()
        url = reverse("linea-list")
        data = {
            "cliente": cliente.pk,
            "linea_numero": 0,
            "estado_linea": EstadoLinea.ACTIVO,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_por_cliente_id(self, auth_client):
        cliente1 = ClienteFactory()
        cliente2 = ClienteFactory()
        LineaServicioFactory(cliente=cliente1)
        LineaServicioFactory(cliente=cliente1)
        LineaServicioFactory(cliente=cliente2)
        url = reverse("linea-list") + f"?cliente_id={cliente1.pk}"
        response = auth_client.get(url)
        assert response.data["count"] == 2

    def test_estado_cobranza_endpoint(self, auth_client):
        linea = LineaServicioFactory()
        url = reverse("linea-estado-cobranza", args=[linea.pk])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "unpaid_count" in response.data
        assert "saldo_vencido" in response.data
        assert "ultimos_logs" in response.data
