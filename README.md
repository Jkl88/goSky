# goSky — сократитель ссылок SkyKraft

Сервис коротких ссылок на FastAPI + Vue 3 с авторизацией через [OAuthSky](/mnt/home/OAuthSky).

## Возможности

- Создание коротких ссылок (код до 6 символов: `A-Z`, `a-z`, `0-9`, `$@!%#`)
- Публичные и приватные ссылки
- QR-код и копирование ссылок по клику
- Режим просмотра: `go.skykraft.su/ABC123/vq`
- Тёмная / светлая / системная тема
- Адаптивный интерфейс для мобильных

## Быстрый старт (dev)

```bash
cp .env.example .env
# Настройте OAUTHSKY_* в .env

docker compose -f docker-compose.dev.yml up --build
```

- Фронтенд: http://localhost:5175
- API: http://localhost:8000
- Postgres: localhost:5433

## OAuthSky

1. В `.env` OAuthSky добавьте клиент (или через bootstrap):

```env
GOSKY_OAUTH_CLIENT_ID=gosky
GOSKY_OAUTH_CLIENT_SECRET=<secret>
GOSKY_REDIRECT_URI=https://go.skykraft.su/api/auth/oauthsky/callback
```

2. В `.env` goSky:

```env
OAUTHSKY_ENABLED=true
OAUTHSKY_URL=https://oauth.skykraft.su
OAUTHSKY_CLIENT_ID=gosky
OAUTHSKY_CLIENT_SECRET=<secret>
PUBLIC_BASE_URL=https://go.skykraft.su
FRONTEND_ORIGIN=https://go.skykraft.su
```

## Продакшен

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Caddy: `deploy/caddy/gosky.conf` → `127.0.0.1:8083` (порт 8082 занят tgapi.skykraft.su)

```bash
./deploy/install-caddy.sh
```

## Маршруты

| URL | Поведение |
|-----|-----------|
| `/{код}` | Редирект на оригинал |
| `/{код}/vq` | Страница просмотра (QR, копирование) |
| `/api/links` | CRUD (авторизация) |
