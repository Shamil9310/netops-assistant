#!/usr/bin/env bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "=============================="
echo "  NetOps Assistant — Setup"
echo "=============================="
echo ""

# --- Check Homebrew ---
if ! command -v brew &>/dev/null; then
  fail "Homebrew не найден. Установи с https://brew.sh"
fi
ok "Homebrew найден"

# --- Check / Install PostgreSQL ---
if ! command -v psql &>/dev/null; then
  warn "PostgreSQL не найден — устанавливаю через brew..."
  brew install postgresql@17
  brew services start postgresql@17
  sleep 2
else
  ok "PostgreSQL найден: $(psql --version)"
  # Запускаем сервис если не запущен
  if ! pg_isready -q; then
    warn "PostgreSQL не запущен — запускаю..."
    brew services start postgresql@17 2>/dev/null || brew services start postgresql 2>/dev/null
    sleep 2
  fi
fi

# --- Create DB ---
DB_NAME="netops_assistant"
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
  ok "База данных '$DB_NAME' уже существует"
else
  createdb "$DB_NAME"
  ok "База данных '$DB_NAME' создана"
fi

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
  fail "Python 3 не найден. Установи через brew: brew install python"
fi
PYTHON_VERSION=$(python3 --version)
ok "Python найден: $PYTHON_VERSION"

# --- Backend venv ---
BACKEND_DIR="$(dirname "$0")/backend"
cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ok "Виртуальное окружение создано"
else
  ok "Виртуальное окружение уже существует"
fi

source .venv/bin/activate
pip install -e . -q
ok "Backend зависимости установлены"

# --- Backend .env ---
if [ ! -f ".env" ]; then
  cp .env.example .env
  # Подставляем текущего пользователя в DATABASE_URL
  CURRENT_USER=$(whoami)
  sed -i '' "s|postgresql+asyncpg://netops:netops@localhost:5432/netops_assistant|postgresql+asyncpg://${CURRENT_USER}@localhost:5432/netops_assistant|" .env
  # Генерируем случайный SECRET_KEY
  SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i '' "s|change-me|${SECRET}|" .env
  ok "Backend .env создан"
else
  ok "Backend .env уже существует"
fi

deactivate
cd ..

# --- Check Node.js ---
if ! command -v node &>/dev/null; then
  fail "Node.js не найден. Установи через brew: brew install node"
fi
ok "Node.js найден: $(node --version)"

# --- Frontend deps ---
FRONTEND_DIR="$(dirname "$0")/frontend"
cd "$FRONTEND_DIR"

npm install -q
ok "Frontend зависимости установлены"

# --- Frontend .env ---
if [ ! -f ".env.local" ]; then
  cp .env.example .env.local
  ok "Frontend .env.local создан"
else
  ok "Frontend .env.local уже существует"
fi

cd ..

# --- Done ---
echo ""
echo "=============================="
echo -e "  ${GREEN}Готово! Запуск проекта:${NC}"
echo "=============================="
echo ""
echo "  Terminal 1 (backend):"
echo "    cd backend"
echo "    source .venv/bin/activate"
echo "    uvicorn app.main:app --reload"
echo ""
echo "  Terminal 2 (frontend):"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "  Открой браузер: http://localhost:3000"
echo "  Логин: engineer / engineer123"
echo ""
