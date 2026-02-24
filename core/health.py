from django.urls import path
from django.http import JsonResponse
from django.db import connection
import redis
from django.conf import settings


def healthcheck(request):
    status = {"status": "ok", "db": "ok", "redis": "ok"}
    http_status = 200

    try:
        connection.ensure_connection()
    except Exception as e:
        status["db"] = str(e)
        status["status"] = "degraded"
        http_status = 503

    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
    except Exception as e:
        status["redis"] = str(e)
        status["status"] = "degraded"
        http_status = 503

    return JsonResponse(status, status=http_status)


urlpatterns = [
    path("", healthcheck, name="healthcheck"),
]
