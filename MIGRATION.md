# Миграция NetOps Assistant на VM (RedOS) — нативная установка

## Архитектура

```
Браузер (15 пользователей)
        │  :80
        ▼
     Nginx
    /       \
   /         \
:3000       :8000
Frontend    Backend (FastAPI)
(Next.js)        │
                 ▼
           PostgreSQL :5432
```

Nginx проксирует всё снаружи — пользователи видят только порт 80.
Frontend и Backend слушают только `localhost` — наружу не торчат.

---

## Требования к VM

| Параметр | Минимум |
|----------|---------|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Disk | 40 GB |
| OS | RedOS 7.3+ |

---

## Шаг 1 — Системные зависимости

```bash
sudo dnf update -y
sudo dnf install -y git curl wget vim gcc make openssl-devel bzip2-devel \
  libffi-devel zlib-devel readline-devel sqlite-devel xz-devel \
  nginx firewalld
```

---

## Шаг 2 — PostgreSQL

### 2.1 Установка

```bash
# Проверить доступную версию
dnf info postgresql-server

# Установить (версия может называться postgresql17-server в некоторых репах)
sudo dnf install -y postgresql-server postgresql
```

> Если в репах только старая версия — добавить официальный репозиторий PostgreSQL:
> ```bash
> sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
> sudo dnf -qy module disable postgresql
> sudo dnf install -y postgresql17-server
> ```

### 2.2 Инициализация и запуск

```bash
# Инициализировать кластер
sudo postgresql-setup --initdb

# Или для postgresql17:
# sudo /usr/pgsql-17/bin/postgresql-17-setup initdb

sudo systemctl enable --now postgresql
```

### 2.3 Создание БД и пользователя

```bash
sudo -u postgres psql <<'SQL'
CREATE USER netops WITH PASSWORD 'ЗАМЕНИ_НА_СИЛЬНЫЙ_ПАРОЛЬ';
CREATE DATABASE netops_assistant OWNER netops ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE netops_assistant TO netops;
SQL
```

### 2.4 Настройка аутентификации

Разрешить подключение локального пользователя `netops` по паролю:

```bash
# Найти файл pg_hba.conf
sudo -u postgres psql -c "SHOW hba_file;"

# Открыть файл
sudo vim /var/lib/pgsql/data/pg_hba.conf
# Или для postgresql17:
# sudo vim /var/lib/pgsql/17/data/pg_hba.conf
```

Добавить строку (перед остальными `local`/`host` правилами):

```
# NetOps Assistant
local   netops_assistant   netops                    scram-sha-256
host    netops_assistant   netops   127.0.0.1/32     scram-sha-256
```

```bash
sudo systemctl restart postgresql
```

### 2.5 Проверка подключения

```bash
psql -h 127.0.0.1 -U netops -d netops_assistant -c "SELECT version();"
# Введёт пароль — должен вернуть версию PostgreSQL
```

---

## Шаг 3 — Python 3.14

### 3.1 Сборка из исходников

Python 3.14 ещё не будет в репозиториях RedOS — собираем сами:

```bash
# Проверить актуальную версию: https://www.python.org/ftp/python/
# Подставить реальный номер вместо 3.14.0bX
PYTHON_VERSION=3.14.0b1   # <-- УТОЧНИТЬ ПЕРЕД ВЫПОЛНЕНИЕМ

cd /opt
sudo curl -O https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
sudo tar -xzf Python-${PYTHON_VERSION}.tgz
cd Python-${PYTHON_VERSION}

sudo ./configure --enable-optimizations --with-ensurepip=install
sudo make -j$(nproc)
sudo make altinstall   # altinstall — не перезаписывает системный python3
```

### 3.2 Проверка

```bash
python3.14 --version   # Python 3.14.x
python3.14 -m pip --version
```

---

## Шаг 4 — Перенос кода

### 4.1 Через Git

```bash
sudo mkdir -p /opt/netops-assistant
sudo chown $USER:$USER /opt/netops-assistant

git clone <URL_репозитория> /opt/netops-assistant
cd /opt/netops-assistant
```

### 4.2 Через архив (если нет доступа к git-серверу)

На локальной машине:

```bash
cd ~/Documents/Projects

tar -czf netops-assistant.tar.gz \
  --exclude='netops-assistant/frontend/node_modules' \
  --exclude='netops-assistant/frontend/.next' \
  --exclude='netops-assistant/backend/.venv' \
  --exclude='netops-assistant/**/__pycache__' \
  --exclude='netops-assistant/.dev_runtime' \
  netops-assistant/

scp netops-assistant.tar.gz user@<VM_IP>:/opt/
```

На VM:

```bash
cd /opt
sudo tar -xzf netops-assistant.tar.gz
sudo chown -R $USER:$USER /opt/netops-assistant
```

---

## Шаг 5 — Backend (FastAPI)

### 5.1 Виртуальное окружение и зависимости

```bash
cd /opt/netops-assistant/backend

python3.14 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e .
```

### 5.2 Переменные окружения

```bash
cp .env.development .env
vim .env
```

Обязательно изменить:

```env
NETOPS_ASSISTANT_SECRET_KEY=<СГЕНЕРИРОВАТЬ: python3.14 -c "import secrets; print(secrets.token_hex(32))">
NETOPS_ASSISTANT_ENVIRONMENT=production
NETOPS_ASSISTANT_DATABASE_URL=postgresql+asyncpg://netops:<ПАРОЛЬ_БД>@127.0.0.1:5432/netops_assistant
NETOPS_ASSISTANT_CORS_ORIGINS=["http://<VM_IP>"]
NETOPS_ASSISTANT_SESSION_COOKIE_SECURE=false
NETOPS_ASSISTANT_SESSION_TTL_HOURS=8
NETOPS_ASSISTANT_BOOTSTRAP_USERNAME=admin
NETOPS_ASSISTANT_BOOTSTRAP_PASSWORD=<СИЛЬНЫЙ_ПАРОЛЬ>
NETOPS_ASSISTANT_BOOTSTRAP_FULL_NAME=Администратор
```

### 5.3 Применить миграции БД

```bash
cd /opt/netops-assistant/backend
source .venv/bin/activate

alembic upgrade head
```

### 5.4 Systemd-сервис для Backend

```bash
sudo tee /etc/systemd/system/netops-backend.service <<'EOF'
[Unit]
Description=NetOps Assistant Backend (FastAPI)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=netops-app
Group=netops-app
WorkingDirectory=/opt/netops-assistant/backend
EnvironmentFile=/opt/netops-assistant/backend/.env
ExecStart=/opt/netops-assistant/backend/.venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

> `--workers 2` — достаточно для 15 пользователей. Можно поднять до 4 если нагрузка вырастет.

### 5.5 Создать системного пользователя для сервиса

```bash
sudo useradd --system --no-create-home --shell /sbin/nologin netops-app
sudo chown -R netops-app:netops-app /opt/netops-assistant/backend
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now netops-backend

# Проверка
sudo systemctl status netops-backend
curl http://127.0.0.1:8000/api/v1/health
```

---

## Шаг 6 — Frontend (Next.js)

### 6.1 Установка Node.js 22

```bash
# Через NodeSource
curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
sudo dnf install -y nodejs

node --version   # v22.x.x
npm --version
```

### 6.2 Сборка

```bash
cd /opt/netops-assistant/frontend

# Создать .env.local
cat > .env.local <<EOF
# Публичный адрес backend — виден браузеру через nginx
NEXT_PUBLIC_API_BASE_URL=http://<VM_IP>

# Внутренний адрес для SSR (Next.js → backend напрямую)
INTERNAL_API_BASE_URL=http://127.0.0.1:8000
EOF

npm install
npm run build
```

### 6.3 Systemd-сервис для Frontend

```bash
sudo tee /etc/systemd/system/netops-frontend.service <<'EOF'
[Unit]
Description=NetOps Assistant Frontend (Next.js)
After=network.target netops-backend.service
Requires=netops-backend.service

[Service]
Type=simple
User=netops-app
Group=netops-app
WorkingDirectory=/opt/netops-assistant/frontend
ExecStart=/usr/bin/node server.js
Environment=PORT=3000
Environment=NODE_ENV=production
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo chown -R netops-app:netops-app /opt/netops-assistant/frontend

sudo systemctl daemon-reload
sudo systemctl enable --now netops-frontend

# Проверка
sudo systemctl status netops-frontend
curl -I http://127.0.0.1:3000
```

---

## Шаг 7 — Nginx

### 7.1 Конфигурация

```bash
sudo tee /etc/nginx/conf.d/netops-assistant.conf <<'EOF'
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name <VM_IP>;   # или домен, если есть

    client_max_body_size 10m;

    # API запросы → backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    # Всё остальное → frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
EOF
```

### 7.2 Проверка и запуск

```bash
sudo nginx -t   # Проверить конфиг — должно быть "syntax is ok"

sudo systemctl enable --now nginx
```

---

## Шаг 8 — Firewall

```bash
# Открыть только 80 (nginx) — backend и frontend не торчат наружу
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload

# Проверка
sudo firewall-cmd --list-services
```

---

## Шаг 9 — Миграция данных (если есть существующая БД)

```bash
# На старой машине — дамп
pg_dump -h localhost -U netops -d netops_assistant -F c -f netops_backup.dump

# Скопировать на VM
scp netops_backup.dump user@<VM_IP>:/opt/

# На VM — восстановить
pg_restore -h 127.0.0.1 -U netops -d netops_assistant --clean netops_backup.dump

# Применить новые миграции (если появились)
cd /opt/netops-assistant/backend
source .venv/bin/activate
alembic upgrade head
```

---

## Финальный чеклист

```
[ ] postgresql запущен: sudo systemctl status postgresql
[ ] netops-backend запущен: sudo systemctl status netops-backend
[ ] netops-frontend запущен: sudo systemctl status netops-frontend
[ ] nginx запущен: sudo systemctl status nginx
[ ] curl http://127.0.0.1:8000/api/v1/health → {"status":"ok"}
[ ] curl -I http://127.0.0.1:3000 → 200 OK
[ ] Открыть http://<VM_IP> в браузере → загружается login
[ ] Войти под admin → успешно
[ ] Создать запись в журнале → сохраняется
[ ] Перезагрузить VM (sudo reboot) → всё поднимается само
```

---

## Полезные команды

```bash
# Логи сервисов
sudo journalctl -u netops-backend -f
sudo journalctl -u netops-frontend -f
sudo journalctl -u nginx -f

# Перезапуск после обновления кода
cd /opt/netops-assistant

# Backend
git pull
cd backend && source .venv/bin/activate && alembic upgrade head && deactivate
sudo systemctl restart netops-backend

# Frontend (требует пересборки)
cd /opt/netops-assistant/frontend
sudo -u netops-app npm run build
sudo systemctl restart netops-frontend
```

---

## Типичные проблемы

| Проблема | Причина | Решение |
|----------|---------|---------|
| Backend не стартует | Неверный `DATABASE_URL` | Проверить пароль БД и pg_hba.conf |
| Frontend не видит API | Неверный `NEXT_PUBLIC_API_BASE_URL` | Указать реальный IP, пересобрать `npm run build` |
| 502 Bad Gateway в nginx | Сервис не запущен | `systemctl status netops-backend` |
| `Secret key too short` | Ключ < 32 символов | `python3.14 -c "import secrets; print(secrets.token_hex(32))"` |
| Python 3.14 не найден | Не сделан `altinstall` | `which python3.14`, проверить `/usr/local/bin/` |
