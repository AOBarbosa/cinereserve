# CineReserve API

A high-performance, scalable RESTful backend for managing cinema operations — movie discovery, real-time seat availability, and ticket reservations with concurrency control.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Features](#features)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Running with Docker](#running-with-docker-recommended)
  - [Running Locally](#running-locally)
- [Seed Data](#seed-data)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Architecture Decisions](#architecture-decisions)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 6.0 + Django REST Framework 3.16 |
| Auth | JWT via `djangorestframework-simplejwt` — stored in HttpOnly cookies |
| Database | PostgreSQL 16 |
| Cache / Locking | Redis 7 via `django-redis` |
| API Docs | Swagger UI + ReDoc via `drf-spectacular` |
| Containerization | Docker + Docker Compose |
| Dependency Management | Poetry |
| Testing | pytest + pytest-django + factory-boy |
| Linting | Ruff |
| CI | GitHub Actions |

---

## Features

### Auth
- Email-based registration and login
- JWT stored in **HttpOnly cookies** (`access_token`, `refresh_token`) — tokens are never exposed in the response body
- Refresh token rotation with blacklisting on logout
- Token verification endpoint

### Movies
- List movies (active only for regular users, all for admins)
- Create, update, and soft-delete movies (admin only)
- Hard delete (admin only)
- Response cached for 5 minutes via Redis

### Sessions & Seats
- List active sessions per movie
- Session list cached for 2 minutes via Redis
- Full seat map for a session with lazy expiry — expired reservations are automatically reverted to available on each seat map request
- Seat auto-generation on session creation (rows × columns, labels A1…Z26)

### Reservations
- Reserve a seat with a **10-minute TTL**
- Distributed lock via Redis (`cache.add` — atomic SET NX) to prevent double-booking under concurrent requests
- Confirm a reservation → seat marked as PURCHASED and ticket issued
- Expired reservations are cleaned up lazily on seat map queries

### Tickets
- Authenticated users can list their confirmed tickets
- Filter by upcoming or past sessions (`?upcoming=true|false`)

### Admin
- List all users (admin only, paginated)
- Full movie management (CRUD + soft delete)

### Performance & Security
- Redis cache on high-read endpoints (movies list, sessions list)
- Rate limiting: 60 req/min for anonymous users, 120 req/min for authenticated users
- Split settings per environment (`development`, `production`, `test`)
- Security headers enabled in production

---

## API Reference

Base URL: `/api/v1/`

### Users

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/users/register/` | Public | Create account |
| POST | `/users/login/` | Public | Login, sets HttpOnly cookies |
| POST | `/users/logout/` | Required | Blacklist refresh token, clear cookies |
| POST | `/users/token/refresh/` | Public | Rotate tokens via cookie |
| POST | `/auth/token/verify/` | Public | Verify a token |
| GET | `/users/` | Admin | List all users (paginated) |
| GET | `/users/tickets/` | Required | List confirmed tickets (`?upcoming=true\|false`) |

### Movies

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/movies/` | Public | List movies |
| POST | `/movies/` | Admin | Create movie |
| GET | `/movies/<id>/` | Public | Retrieve movie |
| PUT | `/movies/<id>/` | Admin | Full update |
| PATCH | `/movies/<id>/` | Admin | Partial update or soft delete (`is_active=false`) |
| DELETE | `/movies/<id>/` | Admin | Hard delete |

### Sessions & Seats

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/movies/<movie_id>/sessions/` | Public | List active sessions for a movie |
| GET | `/movies/<movie_id>/sessions/<session_id>/seats/` | Public | Seat map with lazy expiry |
| POST | `/movies/<movie_id>/sessions/<session_id>/seats/<seat_id>/reserve/` | Required | Reserve a seat (10 min TTL) |
| POST | `/movies/<movie_id>/sessions/<session_id>/seats/<seat_id>/confirm/` | Required | Confirm reservation → PURCHASED |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) — for the containerized setup
- [Python 3.12](https://www.python.org/downloads/) and [Poetry](https://python-poetry.org/docs/#installation) — for local setup

### Environment Variables

Copy the example file and adjust the values as needed:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `cinereserve` |
| `DB_USER` | PostgreSQL user | `cinereserve` |
| `DB_PASSWORD` | PostgreSQL password | `cinereserve` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token expiry (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token expiry (days) | `7` |

---

### Running with Docker (recommended)

This single command builds the image and starts the API, PostgreSQL, and Redis. Migrations and seed data are applied automatically on startup.

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

**Detached mode:**

```bash
docker compose up --build -d
```

**Stop all services:**

```bash
docker compose down
```

**Stop and remove volumes (wipes the database):**

```bash
docker compose down -v
```

---

### Running Locally

**1. Install dependencies:**

```bash
poetry install
```

**2. Start PostgreSQL and Redis via Docker:**

```bash
docker compose up db redis -d
```

**3. Ensure your `.env` points to localhost:**

```dotenv
DB_HOST=localhost
DB_PORT=5433
REDIS_URL=redis://localhost:6379/0
```

**4. Apply migrations:**

```bash
poetry run python manage.py migrate
```

**5. (Optional) Populate the database with seed data:**

```bash
poetry run python manage.py seed
```

**6. Start the development server:**

```bash
poetry run python manage.py runserver
```

The API will be available at `http://localhost:8000`.

---

## Seed Data

The `seed` command is idempotent — safe to run multiple times. It creates:

| Resource | Details |
|---|---|
| User | `user@cinereserve.com` / `User@1234!` |
| Admin | `admin@cinereserve.com` / `Admin@1234!` |
| Movies | *The Dark Knight*, *Inception* |
| Sessions | 6 sessions per movie across rooms A–F (past and future) |
| Seats | Auto-generated per session |
| Tickets | Past and upcoming purchased tickets for the seed user |

---

## Running Tests

Tests use an in-memory SQLite database and a local memory cache — no external services required.

**Run all tests with coverage report:**

```bash
poetry run pytest
```

**Run a specific test file:**

```bash
poetry run pytest apps/sessions/tests/test_reserve_seat.py
```

**Run a specific test class or case:**

```bash
poetry run pytest apps/users/tests/test_auth.py::TestLogout
poetry run pytest apps/users/tests/test_auth.py::TestLogout::test_logout_success_blacklists_refresh_token
```

**Current results:** 166 tests — 100% passing, 94% coverage.

---

## API Documentation

Interactive documentation is available after starting the server:

| Interface | URL |
|---|---|
| Swagger UI | `http://localhost:8000/api/docs/` |
| ReDoc | `http://localhost:8000/api/redoc/` |
| OpenAPI Schema | `http://localhost:8000/api/schema/` |

---

## Architecture Decisions

**JWT stored in HttpOnly cookies**
Tokens are never exposed in the response body. `CookieJWTAuthentication` reads the `access_token` cookie on every request. This prevents XSS attacks from stealing tokens via JavaScript.

**Redis distributed lock for seat reservation**
`cache.add(key, value, timeout)` is an atomic SET NX operation. It returns `True` only if the key did not already exist, guaranteeing that only one request can acquire the lock per seat at a time. After acquiring the lock, the seat status is re-checked from the database (`refresh_from_db`) to handle any race condition between the initial check and the lock acquisition.

**Lazy expiry on seat map**
Instead of a background task, expired reservations are cleaned up when the seat map is requested. Before returning the seats, the view deletes all unconfirmed reservations past their `expires_at` and reverts those seats to `AVAILABLE`. This keeps the infrastructure simple with no need for Celery.

**Redis cache on high-read endpoints**
`GET /movies/` (5 min TTL) and `GET /movies/<id>/sessions/` (2 min TTL) are cached via `cache_page`. These endpoints change rarely and are read frequently, making them ideal cache targets.

**Rate limiting**
`AnonRateThrottle` (60 req/min per IP) and `UserRateThrottle` (120 req/min per user) are applied globally via `DEFAULT_THROTTLE_CLASSES`, protecting the API from abuse without per-view configuration.

**Split settings per environment**
`base.py` holds shared config. `development.py`, `production.py`, and `test.py` each inherit from it and override only what they need. The test settings use SQLite in-memory and `LocMemCache` so the test suite runs without any external services.

**Custom `User` model with email-based login**
`USERNAME_FIELD = "email"` makes email the primary login identifier. Defined from the start to avoid the painful migration required if changed after initial deployment.
