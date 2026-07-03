#!/usr/bin/env bash
# Установка Caddy-конфига для go.skykraft.su
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_SRC="$ROOT/deploy/caddy/gosky.conf"
SITE_DST="/etc/caddy/sites/gosky.conf"

if [[ ! -f "$SITE_SRC" ]]; then
  echo "Не найден: $SITE_SRC" >&2
  exit 1
fi

echo "==> Копирование $SITE_SRC → $SITE_DST"
sudo cp "$SITE_SRC" "$SITE_DST"

echo "==> Проверка конфигурации Caddy"
sudo caddy validate --config /etc/caddy/Caddyfile

echo "==> Перезагрузка Caddy"
sudo systemctl reload caddy

echo "==> Готово. go.skykraft.su → 127.0.0.1:8083"
echo "    Запустите стек: docker compose -f $ROOT/docker-compose.prod.yml up -d --build"
