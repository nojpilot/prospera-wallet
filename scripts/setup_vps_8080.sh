#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/setup_vps_8080.sh"
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

DOMAIN="${DOMAIN:-}"
if [[ -z "$DOMAIN" && -f .env ]]; then
  DOMAIN="$(awk -F= '$1=="DOMAIN"{print substr($0, index($0,$2))}' .env | tail -n1)"
fi
BOT_TOKEN_VALUE="${BOT_TOKEN:-}"
JWT_SECRET_VALUE="${JWT_SECRET:-}"
CERT_FULLCHAIN="${CERT_FULLCHAIN:-}"
CERT_PRIVKEY="${CERT_PRIVKEY:-}"

if [[ -z "$DOMAIN" || -z "$BOT_TOKEN_VALUE" || -z "$JWT_SECRET_VALUE" || -z "$CERT_FULLCHAIN" || -z "$CERT_PRIVKEY" ]]; then
  cat <<'EOF'
Missing required env vars.

Where to put your domain:
- quick run: pass DOMAIN=app.example.com before the script
- persistent: set DOMAIN=app.example.com in .env
- `mini.` prefix is optional; any domain/subdomain that matches your TLS cert is valid

Example:
  DOMAIN=app.example.com \
  BOT_TOKEN=123456:telegram-token \
  JWT_SECRET='super-secret' \
  CERT_FULLCHAIN=/etc/letsencrypt/live/app.example.com/fullchain.pem \
  CERT_PRIVKEY=/etc/letsencrypt/live/app.example.com/privkey.pem \
  sudo bash scripts/setup_vps_8080.sh
EOF
  exit 1
fi

if [[ ! -f "$CERT_FULLCHAIN" || ! -f "$CERT_PRIVKEY" ]]; then
  echo "Certificate files not found. Provide valid TLS cert paths."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

mkdir -p deploy/certs
cp "$CERT_FULLCHAIN" deploy/certs/fullchain.pem
cp "$CERT_PRIVKEY" deploy/certs/privkey.pem
chmod 600 deploy/certs/privkey.pem

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

upsert_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

upsert_env "BOT_TOKEN" "$BOT_TOKEN_VALUE"
upsert_env "JWT_SECRET" "$JWT_SECRET_VALUE"
upsert_env "WEBAPP_URL" "https://${DOMAIN}:8080"
upsert_env "WEBAPP_HOST" "0.0.0.0"
upsert_env "WEBAPP_PORT" "8080"

if ! grep -q "^BOT_WEBHOOK_SECRET=" .env; then
  upsert_env "BOT_WEBHOOK_SECRET" "change-me"
fi
if ! grep -q "^BOT_WEBHOOK_PATH=" .env; then
  upsert_env "BOT_WEBHOOK_PATH" "/telegram/webhook"
fi

docker compose -f docker-compose.yml -f deploy/docker-compose.8080.yml up -d --build

echo "Done. Mini App URL: https://${DOMAIN}:8080"
echo "IMPORTANT: this requires a valid public TLS certificate for ${DOMAIN}."
