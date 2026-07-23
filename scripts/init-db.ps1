Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host 'Waiting for postgres and auth-service to become healthy...'
docker compose up -d postgres redis auth-service hqa-service hqs-service

Write-Host 'Running auth migrations...'
docker compose exec auth-service alembic upgrade head

Write-Host 'Running hqa migrations...'
docker compose exec hqa-service alembic upgrade head

Write-Host 'Seeding auth data (idempotent upsert seed)...'
docker compose exec auth-service python -m app.db.seed

Write-Host 'Database initialization completed.'
