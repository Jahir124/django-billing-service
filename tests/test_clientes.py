import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from apps.clientes.models import Cliente
from .factories import ClienteFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser("admin", "admin@test.com", "admin123")


@pytest.fixture
def regular_user(db):
    return User.objects.create_user("user", "user@test.com", "user123")


@pytest.fixture
def auth_client(api_client, regular_user):
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.mark.django_db
class TestClienteListCreate:
    def test_list_clientes(self, auth_client):
        ClienteFactory.create_batch(3)
        url = reverse("cliente-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_create_cliente_valid(self, auth_client):
        url = reverse("cliente-list")
        data = {
            "identificacion": "0903369387",
            "razon_social": "Test Corp S.A.",
            "email": "test@corp.com",
            "celular": "0999999999",
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Cliente.objects.filter(identificacion="0903369387").exists()

    def test_create_cliente_identificacion_duplicada(self, auth_client):
        ClienteFactory(identificacion="0903369387")
        url = reverse("cliente-list")
        data = {"identificacion": "0903369387", "razon_social": "Otro"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_cliente_identificacion_invalida(self, auth_client):
        url = reverse("cliente-list")
        data = {"identificacion": "123", "razon_social": "Test"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_por_razon_social(self, auth_client):
        ClienteFactory(razon_social="Claro Ecuador")
        ClienteFactory(razon_social="CNT EP")
        url = reverse("cliente-list") + "?razon_social=claro"
        response = auth_client.get(url)
        assert response.data["count"] == 1

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("cliente-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestClienteDetail:
    def test_soft_delete_by_admin(self, admin_client):
        cliente = ClienteFactory()
        url = reverse("cliente-detail", args=[cliente.pk])
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        cliente.refresh_from_db()
        assert cliente.is_active is False

    def test_soft_delete_non_admin_forbidden(self, auth_client):
        cliente = ClienteFactory()
        url = reverse("cliente-detail", args=[cliente.pk])
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_updates_fields(self, auth_client):
        cliente = ClienteFactory(razon_social="Viejo Nombre")
        url = reverse("cliente-detail", args=[cliente.pk])
        response = auth_client.patch(url, {"razon_social": "Nuevo Nombre"})
        assert response.status_code == status.HTTP_200_OK
        cliente.refresh_from_db()
        assert cliente.razon_social == "Nuevo Nombre"

    def test_delete_ya_eliminado_returns_409(self, admin_client):
        cliente = ClienteFactory(is_active=False)
        url = reverse("cliente-detail", args=[cliente.pk])
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_409_CONFLICT
