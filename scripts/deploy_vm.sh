#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/corp.tele2.ru/admin.isaev/netops-assistant"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

echo "[deploy] project root: ${PROJECT_ROOT}"

cd "${PROJECT_ROOT}"
git pull --ff-only origin main

echo "[deploy] backend"
cd "${BACKEND_DIR}"
source .venv/bin/activate
pip install -e .
alembic upgrade head

echo "[deploy] frontend"
cd "${FRONTEND_DIR}"
npm install
npm run build

echo "[deploy] restart services"
sudo systemctl restart netops-backend
sudo systemctl restart netops-frontend

echo "[deploy] wait for backend"
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null; then
    echo "[deploy] backend is up"
    break
  fi
  sleep 1
done

echo "[deploy] wait for frontend"
for i in $(seq 1 30); do
  if curl -fsSI http://127.0.0.1:3000/login >/dev/null; then
    echo "[deploy] frontend is up"
    break
  fi
  sleep 1
done

echo "[deploy] health checks"
curl -fsS http://127.0.0.1:8000/api/v1/health
curl -fsSI http://127.0.0.1:3000/login

echo
echo "[deploy] done"
