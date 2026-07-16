# Auth Security Suite

FastAPI application for automated login security testing using Playwright. Supports REST API control, CLI execution, and Docker + nginx deployment.

## Project structure

```
auth-security-suite/
├── .env.example              # Environment variable template
├── Dockerfile                # Playwright-based app image
├── docker-compose.yml        # App + nginx stack
├── nginx/nginx.conf          # Reverse proxy config
├── pyproject.toml
├── requirements.txt
└── src/auth_security_suite/
    ├── main.py               # FastAPI app (uvicorn entry)
    ├── cli.py                # CLI runner
    ├── core/settings.py      # .env config (pydantic-settings)
    ├── schemas/              # Request/response models
    ├── services/             # Login tester + password generator
    ├── worker/               # Background job runner
    └── api/v1/endpoints/     # REST endpoints
```

## Prerequisites

- Python 3.11+
- [Playwright](https://playwright.dev/python/) Chromium browser
- Docker & Docker Compose (for containerised deployment)

---

## Configuration

Copy the example env file and edit values for your target site:

```bash
cd auth-security-suite
cp .env.example .env
```

Key variables (all prefixed with `AUTH_SECURITY_`):

| Variable | Description | Example |
|----------|-------------|---------|
| `BASE_URL` | Target auth base URL | `https://issuer-evrc.viitorcloud.in/auth` |
| `LOGIN_EMAIL` | Email used in the login form | `user@example.com` |
| `START_LENGTH` | Initial password length | `8` |
| `START_FROM` | Resume from this password (empty = from beginning) | `000001*E` |
| `HEADLESS` | Run browser without UI | `true` |

**Start from the beginning:**

```env
AUTH_SECURITY_START_FROM=
```

**Resume from a previous run:**

```env
AUTH_SECURITY_START_FROM=000001*E
```

---

## Local development

### 1. Install dependencies

```bash
cd auth-security-suite
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -e .
playwright install chromium
```

### 2. Run the API server

```bash
uvicorn auth_security_suite.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 3. Run via CLI (standalone script)

Uses `.env` settings directly — no API server needed:

```bash
python -m auth_security_suite.cli
```

Or, after install:

```bash
auth-security-suite
```

### 4. Legacy entry point

The original script path still works if the package is installed:

```bash
python python_script/brute_force.py
```

---

## API usage

### Start a job (from the beginning)

```bash
curl -X POST http://localhost:8000/api/v1/brute-force/start \
  -H "Content-Type: application/json" \
  -d '{"start_length": 8, "start_from": null}'
```

### Start a job (resume)

```bash
curl -X POST http://localhost:8000/api/v1/brute-force/start \
  -H "Content-Type: application/json" \
  -d '{"start_length": 8, "start_from": "000001*E"}'
```

### Check status

```bash
curl http://localhost:8000/api/v1/brute-force/status
```

### Stop a running job

```bash
curl -X POST http://localhost:8000/api/v1/brute-force/stop
```

---

## Docker deployment

### 1. Prepare environment

```bash
cd auth-security-suite
cp .env.example .env
# Edit .env with your target site credentials
```

### 2. Build and start

```bash
docker compose up --build -d
```

### 3. Verify

```bash
# Health check via nginx
curl http://localhost:8080/health

# API docs
# Open http://localhost:8080/docs in a browser
```

### 4. View logs

```bash
docker compose logs -f app
```

### 5. Stop

```bash
docker compose down
```

### Services

| Service | Internal port | Exposed port | Description |
|---------|--------------|--------------|-------------|
| `app` | 8000 | — | FastAPI + Playwright |
| `nginx` | 80 | 8080 | Reverse proxy |

---

## How it works

1. **Password generation** — `tiered_combinations()` produces candidates of a given length that contain at least one special character.
2. **Login attempt** — `LoginTester.try_password()` fills the form, clicks Sign In, and checks for a dashboard redirect.
3. **reCAPTCHA handling** — On "Invalid reCAPTCHA" the page reloads and the next password is tried.
4. **Length escalation** — When all combinations for length N are exhausted, the runner moves to length N+1.
5. **Resume support** — Set `START_FROM` to skip already-tried passwords and continue from a saved point.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `TimeoutError` on dashboard wait | Increase `AUTH_SECURITY_NAV_TIMEOUT_MS` in `.env` |
| reCAPTCHA blocks every attempt | Set `AUTH_SECURITY_HEADLESS=false` and solve manually, or add delays |
| `playwright install` missing | Run `playwright install chromium` after pip install |
| Port 8080 already in use | Change nginx port in `docker-compose.yml` |
