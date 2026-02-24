import django_filters
from .models import LineaServicio


class LineaServicioFilter(django_filters.FilterSet):
    cliente_id = django_filters.NumberFilter(field_name="cliente__id")
    estado_linea = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = LineaServicio
        fields = ["cliente_id", "estado_linea", "is_active"]
