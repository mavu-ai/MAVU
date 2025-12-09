# Установка и настройка MAVU

## Требования к системе

### Минимальные требования
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Weaviate 1.23+
- 4GB RAM
- 10GB свободного места

### Рекомендуемые требования
- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Redis 7+
- Weaviate последней версии
- 8GB RAM
- 20GB SSD

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-org/mavuai.git
cd mavuai
```

### 2. Настройка окружения

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend

```bash
cd ../frontend
npm install
```

### 3. Настройка переменных окружения

Создайте файл `.env` в папке `backend/`:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-realtime-preview-2024-10-01

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mavuai
REDIS_URL=redis://localhost:6379

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=optional_for_local

# Security
JWT_SECRET=your_jwt_secret
ADMIN_SECRET=your_admin_secret

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_WEBAPP_URL=https://your-webapp.com
```

### 4. Инициализация базы данных

```bash
cd backend

# Создание базы данных
createdb mavuai

# Применение миграций
alembic upgrade head

# Заполнение начальными данными (опционально)
python -m cli seed-database
```

### 5. Запуск Weaviate

#### Docker Compose (рекомендуется)

```yaml
# docker-compose.yml
version: '3.8'

services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  weaviate_data:
```

```bash
docker-compose up -d
```

### 6. Инициализация Weaviate коллекций

```bash
cd backend
python -m cli init-weaviate
```

### 7. Запуск приложения

#### Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm run dev
```

## Проверка установки

### 1. Проверка Backend

```bash
curl http://localhost:8000/health
# Ответ: {"status": "healthy", "services": {...}}
```

### 2. Проверка Frontend

Откройте браузер: http://localhost:5173

### 3. Проверка Weaviate

```bash
curl http://localhost:8080/v1/.well-known/ready
# Ответ: HTTP 200
```

### 4. Запуск тестов

```bash
cd backend
pytest tests/

cd ../frontend
npm test
```

## Настройка для продакшена

### 1. Использование Docker

```bash
# Build образов
docker build -t mavuai-backend ./backend
docker build -t mavuai-frontend ./frontend

# Запуск через docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Настройка NGINX

```nginx
server {
    listen 80;
    server_name mavu.ai;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    # WebSocket для realtime
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 3. SSL сертификаты

```bash
# Установка Certbot
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d mavu.ai -d www.mavu.ai
```

### 4. Мониторинг и логирование

#### Prometheus метрики

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'mavuai'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
```

#### Sentry для ошибок

```env
SENTRY_DSN=your_sentry_dsn
SENTRY_ENVIRONMENT=production
```

## Решение частых проблем

### 1. OpenAI API ошибки

```
Error: OpenAI API key is invalid
```
**Решение**: Проверьте OPENAI_API_KEY и наличие доступа к realtime API.

### 2. Weaviate не подключается

```
Error: Failed to connect to Weaviate
```
**Решение**:
- Убедитесь, что Weaviate запущен
- Проверьте порты 8080 и 50051
- Проверьте WEAVIATE_URL в .env

### 3. Redis connection refused

```
Error: Redis connection refused
```
**Решение**:
```bash
# Запустите Redis
redis-server

# Или через Docker
docker run -d -p 6379:6379 redis
```

### 4. Database migration failed

```
Error: alembic.util.exc.CommandError
```
**Решение**:
```bash
# Сброс миграций
alembic downgrade base
alembic upgrade head
```

## Дополнительная конфигурация

### Настройка RAG

```python
# backend/config.py

# RAG параметры
RAG_TOP_K_USER = 5  # Количество пользовательских контекстов
RAG_TOP_K_APP = 3   # Количество общих контекстов
RAG_CHUNK_SIZE = 500  # Размер чанков текста
RAG_CHUNK_OVERLAP = 50  # Перекрытие чанков
```

### Настройка голосов и персонажей

```python
# backend/config.py

SKINS = {
    1: {"name": "Рыжий кот", "voice": "shimmer"},
    2: {"name": "Фиолетовая девочка", "voice": "alloy"},
    # Добавьте свои персонажи
}
```

### Настройка детекции угроз

```python
# backend/patterns/threat_patterns.py

THREAT_PATTERNS = {
    "high_risk": [
        r"хочу умереть",
        r"убить себя",
        # Добавьте паттерны
    ]
}
```

## Поддержка

- [GitHub Issues](https://github.com/your-org/mavuai/issues)
- Email: support@mavu.ai
- Telegram: @mavuai_support