# 🧾 Django Billing Service

A production-ready REST API for managing ISP customers, service lines, and automated debt collection — built with Django, Celery, Redis and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)
![Celery](https://img.shields.io/badge/Celery-5.3-brightgreen?logo=celery)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)

---

## 📋 Overview

This service handles:
- **Customer & Service Line management** — full CRUD with soft delete and business validations
- **Billing (Rubros)** — charge records with payment status tracking
- **Automated debt collection** — a Celery Beat task runs every 5 minutes, detects overdue charges, suspends delinquent lines, and reactivates them when paid
- **Full audit trail** — every execution is logged with timestamps, actions taken and error handling

---

## 🏗️ Architecture

```
┌──────────┐    HTTP     ┌──────────────┐
│  Client  │ ──────────► │  Django/DRF  │
│  (API)   │             │   :8000      │
└──────────┘             └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │  PostgreSQL  │
                         └──────────────┘

┌─────────────┐   tasks   ┌──────────────┐
│ Celery Beat │ ────────► │    Redis     │
│ (5 min)     │           │   (broker)   │
└─────────────┘           └──────┬───────┘
                                 │
                          ┌──────▼───────┐
                          │Celery Worker │
                          │ (collections)│
                          └──────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Auth | JWT (SimpleJWT) |
| Async tasks | Celery 5.3 + Celery Beat |
| Broker | Redis 7 |
| Database | PostgreSQL 15 |
| Containers | Docker + docker-compose |
| Docs | OpenAPI / Swagger (drf-spectacular) |
| Tests | pytest + factory-boy |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/Jahir124/django-billing-service.git
cd django-billing-service

# 2. Set up environment variables
cp .env.example .env

# 3. Build and start all services
docker-compose up --build -d

# 4. Run migrations
docker-compose exec web python manage.py makemigrations clientes lineas cobranza
docker-compose exec web python manage.py migrate

# 5. Create admin user
docker-compose exec web python manage.py createsuperuser

# 6. Verify everything is running
curl http://localhost:8000/health/
# Expected: {"status": "ok", "db": "ok", "redis": "ok"}
```

### Services started by docker-compose

| Service | Port | Description |
|---|---|---|
| `web` | 8000 | Django + DRF API |
| `db` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Redis 7 (broker) |
| `celery_worker` | — | Task worker |
| `celery_beat` | — | Periodic scheduler (every 5 min) |

---

## 🔑 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key |
| `DEBUG` | `False` | Debug mode |
| `POSTGRES_DB` | `isp_db` | Database name |
| `POSTGRES_USER` | `isp_user` | Database user |
| `POSTGRES_PASSWORD` | `isp_pass` | Database password |
| `POSTGRES_HOST` | `db` | Database host |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL |

---

## 📡 API Endpoints

### Authentication
```
POST /api/auth/token/         → Get access + refresh token
POST /api/auth/token/refresh/ → Refresh access token
```

### Customers (Clientes)
```
GET    /api/clientes/         → List (filter by identificacion, razon_social)
POST   /api/clientes/         → Create
GET    /api/clientes/{id}/    → Detail
PATCH  /api/clientes/{id}/    → Partial update
DELETE /api/clientes/{id}/    → Soft delete (admin only)
```

### Service Lines (Líneas)
```
GET    /api/lineas/                      → List (filter by cliente_id, estado_linea)
POST   /api/lineas/                      → Create
GET    /api/lineas/{id}/                 → Detail
PATCH  /api/lineas/{id}/                 → Partial update
DELETE /api/lineas/{id}/                 → Soft delete (admin only)
GET    /api/lineas/{id}/estado-cobranza/ → Billing summary + last logs
```

### Billing (Rubros)
```
GET    /api/rubros/                    → List
POST   /api/rubros/                    → Create
PATCH  /api/rubros/{id}/               → Partial update
POST   /api/rubros/ejecutar-cobranza/  → Trigger collection task manually (admin only)
```

### Logs
```
GET /api/cobranza-logs/      → List execution logs
GET /api/cobranza-logs/{id}/ → Log detail
```

### Utilities
```
GET /health/    → Healthcheck (DB + Redis status)
GET /api/docs/  → Swagger UI
```

---

## ⚡ Collection Task Logic

The `proceso_control_morosidad` task runs **every 5 minutes** via Celery Beat:

```
For each active service line (ACTIVO or SUSPENDIDO):
    │
    ├── Find overdue unpaid charges (estado=NO_PAGADO AND fecha_vencimiento < now)
    │
    ├── unpaid_count > 0?
    │   ├── YES → estado_linea = SUSPENDIDO, action = SUSPEND
    │   └── NO  → if was SUSPENDIDO → estado_linea = ACTIVO, action = UNSUSPEND
    │
    ├── Update saldo_vencido = SUM of overdue charges
    │
    └── Save CollectionsRequestLog (started_at, finished_at, status, action_taken)
```

**Key design decisions:**
- Lines with `NO_INSTALADO` or `CANCELADO` status are excluded from processing
- Task is **idempotent** — running it twice produces the same result
- Each line is processed in its own `transaction.atomic()` — one failure doesn't abort the rest
- Uses `select_related` and `aggregate(Sum)` to avoid N+1 queries

---

## 🧪 Running Tests

```bash
pytest
```

Test coverage includes:
- Model validations (identificacion format, linea_numero >= 1, inactive customer rules)
- CRUD endpoints (creation, filters, soft delete, permissions)
- Collection task logic (suspension, reactivation, idempotency, edge cases)

---

## 📬 Postman Collection

Import `django_billing_api.postman_collection.json` into Postman to get all endpoints pre-configured with automatic JWT token handling.

---

## 📁 Project Structure

```
django-billing-service/
├── core/                   # Django settings, celery, urls, healthcheck
├── apps/
│   ├── clientes/           # Customer model + CRUD
│   ├── lineas/             # Service line model + CRUD + billing endpoint
│   └── cobranza/           # Rubro, logs, Celery task
├── tests/                  # pytest test suite + factories
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```
