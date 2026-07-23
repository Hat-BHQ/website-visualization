# website-visualization

## Step 7 - Docker Compose End-to-End

This repository is wired to run the full stack with one command:

```powershell
docker compose up --build
```

Main containers:

- `portal-web`
- `nginx`
- `auth-service`
- `hqa-service`
- `hqa-worker`
- `hqa-beat`
- `hqs-service`
- `postgres`
- `redis`

## 1) Prepare environment (Windows PowerShell)

```powershell
Copy-Item .env.example .env
```

Set required values in `.env`:

- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`
- `SEED_DEFAULT_PASSWORD`
- `GOOGLE_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE`

## 2) Google credential setup

1. Create folder `secrets` in repo root.
2. Put your service account JSON file there, for example:

```text
secrets/google-service-account.json
```

3. Ensure `.env` has:

```text
GOOGLE_SERVICE_ACCOUNT_FILE=/run/secrets/google-service-account.json
```

4. Share your Google Sheet with the service account email as Editor.
5. Set `GOOGLE_SPREADSHEET_ID` to the target Sheet ID.

## 3) Start stack

```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f
```

## 4) Database bootstrap and migration

PostgreSQL creates `auth_db`, `hqa_db`, `hqs_db` automatically on first startup via:

- `infra/postgres/init/01-create-databases.sql`

Run migrations and seed:

```powershell
docker compose exec auth-service alembic upgrade head
docker compose exec auth-service python -m app.db.seed
docker compose exec hqa-service alembic upgrade head
```

One-shot helper:

```powershell
./scripts/init-db.ps1
```

Seed script is idempotent (upsert), so re-running will not duplicate users/modules.

## 5) Service URLs

- Portal (through Nginx): `http://localhost:8080`
- Auth API: `http://localhost:8080/api/auth/`
- HQA API: `http://localhost:8080/api/hqa/`
- HQS API: `http://localhost:8080/api/hqs/`

## 6) Demo accounts

Password is `SEED_DEFAULT_PASSWORD`.

- `admin.hqa@company.com` (HQA Admin)
- `user.hqa@company.com` (HQA User)
- `admin.hqs@company.com` (HQS Admin)
- `user.hqs@company.com` (HQS User)
- `root@company.com` (Superadmin)

## 7) Smoke test checklist

Run baseline commands:

```powershell
docker compose config
docker compose up --build -d
docker compose ps
```

Then validate:

1. All containers are `running` and backend dependencies are healthy.
2. Open `http://localhost:8080`.
3. Login with `admin.hqa@company.com`.
4. Module selector shows HQA for HQA Admin.
5. Open HQA Dashboard.
6. Click eBay sync and verify a job ID appears.
7. Check worker receives job:

```powershell
docker compose logs -f hqa-worker
```

8. Verify sync history updates on dashboard.
9. Verify listings appear from PostgreSQL-backed API.
10. Login as `user.hqa@company.com` and verify sync action is forbidden (403 behavior).
11. Login as `user.hqs@company.com` and verify HQA route is blocked.
12. Restart stack and confirm data persists:

```powershell
docker compose down
docker compose up -d
docker compose ps
```

## 8) Useful operations

Logs per service:

```powershell
docker compose logs -f nginx
docker compose logs -f auth-service
docker compose logs -f hqa-service
docker compose logs -f hqa-worker
docker compose logs -f hqa-beat
docker compose logs -f hqs-service
```

Stop system:

```powershell
docker compose down
```

Stop and remove volumes:

```powershell
docker compose down -v
```