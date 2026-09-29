# TaskFlow API

A production-style task management REST API built with **FastAPI**, **PostgreSQL**, and **Redis**, containerized with **Docker** and deployed to **AWS EC2** via a **GitHub Actions CI/CD pipeline**.

## Why this project exists

This isn't a toy CRUD app. It demonstrates:
- Designing a relational schema (PostgreSQL) alongside a NoSQL-style cache layer (Redis)
- Building secure, validated REST APIs with JWT authentication
- Containerizing an app for reproducible environments
- Automating tests, builds, and deployment with CI/CD
- Basic observability (health checks, structured logging)

## Architecture

```
Client
  │
  ▼
FastAPI (Uvicorn) ──────► PostgreSQL (users, tasks — relational, source of truth)
  │
  └──────────────────────► Redis (caching hot task lists, rate limiting)

CI/CD: GitHub Actions
  push to main → run tests → build Docker image → push to registry → deploy to EC2
```

## Tech stack

| Layer          | Choice                          |
|-----------------|----------------------------------|
| API framework    | FastAPI                         |
| Database          | PostgreSQL (SQLAlchemy ORM)     |
| Cache              | Redis                           |
| Auth                | JWT (python-jose + passlib)     |
| Validation           | Pydantic v2                     |
| Containerization       | Docker + docker-compose         |
| CI/CD                    | GitHub Actions                  |
| Deployment target          | AWS EC2 (or ECS — see notes)    |

## Features

- User registration + login with hashed passwords and JWT access tokens
- Full CRUD on tasks, scoped per authenticated user
- Pagination, filtering (by status), and sorting on the task list endpoint
- Redis-backed caching of a user's task list (invalidated on write)
- Centralized error handling with consistent JSON error responses
- `/health` endpoint for uptime checks / load balancer probes
- Auto-generated OpenAPI docs at `/docs`

## Local setup

```bash
git clone <your-repo-url>
cd taskflow-api
cp .env.example .env          # fill in secrets
docker-compose up --build
```

API will be live at `http://localhost:8000/docs`.

## Running tests

```bash
docker-compose exec api pytest -v
```

## Environment variables

See `.env.example`. Never commit a real `.env` file.

## Deployment (AWS EC2)

1. Launch an EC2 instance (t2.micro is enough for a demo), open port 8000 (or 80 behind Nginx) in the security group.
2. Install Docker + docker-compose on the instance.
3. The GitHub Actions workflow in `.github/workflows/ci-cd.yml` SSHes into the instance on every push to `main`, pulls the latest image, and restarts the container.
4. Required GitHub repo secrets: `EC2_HOST`, `EC2_SSH_KEY`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.

## Project structure

```
taskflow-api/
├── app/
│   ├── main.py          # app entrypoint, routes registered here
│   ├── database.py       # SQLAlchemy engine/session + Redis client
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── auth.py               # password hashing, JWT creation/verification
│   ├── crud.py                 # DB access functions
│   └── routers/
│       ├── auth.py               # /register, /login
│       └── tasks.py               # /tasks CRUD
├── tests/
│   └── test_main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .github/workflows/ci-cd.yml
```

## Resume bullet (suggested)

> Built and deployed a JWT-authenticated task management REST API (FastAPI, PostgreSQL, Redis) with a GitHub Actions CI/CD pipeline auto-deploying Dockerized builds to AWS EC2 on every merge to main.
