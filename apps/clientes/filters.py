import django_filters
from .models import Cliente


class ClienteFilter(django_filters.FilterSet):
    identificacion = django_filters.CharFilter(lookup_expr="icontains")
    razon_social = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Cliente
        fields = ["identificacion", "razon_social", "is_active"]
