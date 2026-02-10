# Prospera Wallet – Telegram Shared Expense Wallet

Production-oriented shared finance backend with Telegram bot + Mini App authentication.

## Stack
- FastAPI API service
- Separate Telegram webhook bot service (aiogram)
- PostgreSQL + SQLAlchemy + Alembic
- JWT auth + Telegram Mini App initData verification
- Structured JSON logs + request IDs + audit logs
- Rate limiting middleware

## Architecture
- `app/main.py` – API service (OpenAPI at `/docs`)
- `app/bot/service.py` – Telegram bot webhook process
- `app/db/models.py` – domain entities
- `app/services/*` – business logic (balances, settlements, transfers)
- `alembic/versions/*` – schema migrations

## Domain entities
Implemented entities:
- User
- Workspace
- Membership
- Wallet
- Category
- Transaction
- TransactionSplit
- FxRate

## Security model
### Option A (implemented): Custodial
- Server stores wallet balances.
- No private keys stored.

### Option B (future)
- Non-custodial signing in client/Mini App.
- Server verifies signed payloads only.

Current controls:
- JWT access tokens
- Telegram initData validation (`/api/v1/auth/telegram-miniapp`)
- Webhook secret validation in bot service
- Rate limiting middleware
- Audit entries for expense/settlement/transfer operations

## API endpoints
- `POST /api/v1/users/register`
- `POST /api/v1/auth/telegram-miniapp`
Mini App HTTP endpoints (served by `app/web_server.py`):
- `GET /api/status`
- `POST /api/expense`
- `POST /api/income`
- `GET /api/balance`
- `GET /api/report`

## Bot commands
- `/start`
- `/open` – open Mini App
- `/setup <name> [CUR]` – create workspace
- `/join <workspace_id>` – join workspace
- `/workspace [id]` – list/switch workspace
- `/wallets` – list wallets
- `/wallet_add <name> <CUR> [shared|personal]`
- `/categories [expense|income]`
- `/category_add <name> [expense|income]`
- `/add <amount> [CUR] <category> [note]`
- `/income <amount> [CUR] <category> [note]`
- `/balance` – who owes whom
- `/report` – monthly expense report

## Run with Docker Compose
```bash
docker-compose up --build
```

## Local development
```bash
cp .env.example .env
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

## Testing strategy implemented
- Unit test: deterministic settlement simplification
- Integration-like test: workspace balances + expense computation

## Future-ready design notes
Designed for extension to:
- multi-currency groups
- on-chain settlement adapters (EVM/TON)
- recurring expenses
- budget policies and anomaly/fraud checks

## Deploy Mini App on external HTTPS :8080 (VPS)
If 80/443 are busy, you can expose Mini App via `https://your-domain:8080` (any FQDN works; `mini.` is optional).

Added files:
- `deploy/nginx-miniapp-8080.conf` – nginx TLS reverse proxy config for the Mini App on `:8080`
- `deploy/nginx-bot-8443.conf` – nginx TLS reverse proxy config for the bot webhook on `:8443`
- `scripts/setup_vps_8080.sh` – one-shot VPS setup script

### Prerequisites
- DNS `A` record for your domain to VPS IP
- Valid TLS certificate for the same domain (e.g. Let's Encrypt)


### Where to put your domain
- `mini.` prefix is **not required**. You can use root domain (`example.com`) or any subdomain (`app.example.com`, `wallet.example.com`).
- **Option A (recommended for first run):** pass it inline in command as `DOMAIN=app.example.com`.
- **Option B (persistent):** save `DOMAIN=app.example.com` in `.env`, then you can run script without passing `DOMAIN` each time.

### One-command setup
```bash
DOMAIN=app.example.com \
BOT_TOKEN=123456:telegram-token \
JWT_SECRET='change-me' \
CERT_FULLCHAIN=/etc/letsencrypt/live/app.example.com/fullchain.pem \
CERT_PRIVKEY=/etc/letsencrypt/live/app.example.com/privkey.pem \
sudo bash scripts/setup_vps_8080.sh
```

After setup, these env vars are set:
- `WEBAPP_URL=https://app.example.com:8080`
- `BOT_WEBHOOK_URL=https://app.example.com:8443`

> Security note: external `8080` is safe only when TLS is enabled (HTTPS).
