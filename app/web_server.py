from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aiohttp import web

from app.config import load_settings
from app.db.session import async_session_factory
from app.services.balance import calculate_balances, format_balance_report, get_workspace_members
from app.services.categories import get_or_create_category
from app.services.reporting import monthly_expense_report
from app.services.transactions import create_expense, create_income
from app.services.users import ensure_user_from_payload
from app.services.utils import normalize_currency, parse_amount_to_minor
from app.services.wallets import get_default_wallet
from app.services.workspaces import get_active_workspace
from app.webapp_auth import WebAppAuthError, extract_user, validate_init_data

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"


def json_error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": message}, status=status)


def json_ok(payload: dict[str, Any]) -> web.Response:
    payload = {"ok": True, **payload}
    return web.json_response(payload)


async def _get_user_payload(
    request: web.Request,
) -> tuple[dict[str, Any], web.Response | None]:
    settings = request.app["settings"]
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    try:
        data = validate_init_data(init_data, settings.bot_token)
        user_payload = extract_user(data)
    except WebAppAuthError as exc:
        return {}, json_error(str(exc), status=401)
    return user_payload, None


async def handle_index(request: web.Request) -> web.Response:
    return web.FileResponse(WEB_DIR / "index.html")


async def handle_status(request: web.Request) -> web.Response:
    user_payload, error = await _get_user_payload(request)
    if error:
        return error

    async with async_session_factory() as session:
        user = await ensure_user_from_payload(session, user_payload)
        workspace = await get_active_workspace(session, user)
    if workspace is None:
        return json_error("no_active_workspace", status=409)

    return json_ok(
        {
            "user": {
                "id": user_payload.get("id"),
                "first_name": user_payload.get("first_name"),
                "last_name": user_payload.get("last_name"),
                "username": user_payload.get("username"),
            },
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "base_currency": workspace.base_currency,
            },
        }
    )


async def _parse_payload(request: web.Request) -> tuple[dict[str, Any] | None, web.Response | None]:
    if request.content_type != "application/json":
        return None, json_error("content_type_must_be_json")
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return None, json_error("invalid_json")
    if not isinstance(payload, dict):
        return None, json_error("invalid_payload")
    return payload, None


async def handle_expense(request: web.Request) -> web.Response:
    user_payload, error = await _get_user_payload(request)
    if error:
        return error

    payload, payload_error = await _parse_payload(request)
    if payload_error:
        return payload_error

    amount_raw = payload.get("amount")
    category_name = payload.get("category")
    note = payload.get("note")
    currency_raw = payload.get("currency")

    if amount_raw is None or category_name is None:
        return json_error("amount_and_category_required")

    async with async_session_factory() as session:
        user = await ensure_user_from_payload(session, user_payload)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            return json_error("no_active_workspace", status=409)

        currency = normalize_currency(str(currency_raw or workspace.base_currency))
        try:
            amount_minor = parse_amount_to_minor(str(amount_raw), currency)
        except ValueError:
            return json_error("invalid_amount")
        if amount_minor <= 0:
            return json_error("amount_must_be_positive")

        wallet = await get_default_wallet(session, workspace, user, currency)
        if wallet is None:
            return json_error("wallet_missing")
        category = await get_or_create_category(session, workspace, str(category_name), "expense")
        tx = await create_expense(
            session,
            workspace=workspace,
            wallet=wallet,
            amount_minor=amount_minor,
            currency=currency,
            note=str(note) if note else None,
            payer=user,
            category_id=category.id,
        )

    return json_ok(
        {
            "transaction_id": tx.id,
            "amount_minor": tx.amount_minor,
            "currency": tx.currency,
        }
    )


async def handle_income(request: web.Request) -> web.Response:
    user_payload, error = await _get_user_payload(request)
    if error:
        return error

    payload, payload_error = await _parse_payload(request)
    if payload_error:
        return payload_error

    amount_raw = payload.get("amount")
    category_name = payload.get("category")
    note = payload.get("note")
    currency_raw = payload.get("currency")

    if amount_raw is None or category_name is None:
        return json_error("amount_and_category_required")

    async with async_session_factory() as session:
        user = await ensure_user_from_payload(session, user_payload)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            return json_error("no_active_workspace", status=409)

        currency = normalize_currency(str(currency_raw or workspace.base_currency))
        try:
            amount_minor = parse_amount_to_minor(str(amount_raw), currency)
        except ValueError:
            return json_error("invalid_amount")
        if amount_minor <= 0:
            return json_error("amount_must_be_positive")

        wallet = await get_default_wallet(session, workspace, user, currency)
        if wallet is None:
            return json_error("wallet_missing")
        category = await get_or_create_category(session, workspace, str(category_name), "income")
        tx = await create_income(
            session,
            workspace=workspace,
            wallet=wallet,
            amount_minor=amount_minor,
            currency=currency,
            note=str(note) if note else None,
            recipient=user,
            category_id=category.id,
        )

    return json_ok(
        {
            "transaction_id": tx.id,
            "amount_minor": tx.amount_minor,
            "currency": tx.currency,
        }
    )


async def handle_balance(request: web.Request) -> web.Response:
    user_payload, error = await _get_user_payload(request)
    if error:
        return error

    async with async_session_factory() as session:
        user = await ensure_user_from_payload(session, user_payload)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            return json_error("no_active_workspace", status=409)
        balances = await calculate_balances(session, workspace)
        members = await get_workspace_members(session, workspace)
    report = format_balance_report(balances, members)
    return json_ok({"report": report})


async def handle_report(request: web.Request) -> web.Response:
    user_payload, error = await _get_user_payload(request)
    if error:
        return error

    async with async_session_factory() as session:
        user = await ensure_user_from_payload(session, user_payload)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            return json_error("no_active_workspace", status=409)
        report = await monthly_expense_report(session, workspace)

    return json_ok({"report": report})


def create_app() -> web.Application:
    app = web.Application()
    app["settings"] = load_settings()

    app.router.add_get("/", handle_index)
    app.router.add_static("/static/", WEB_DIR, show_index=False)

    app.router.add_get("/api/status", handle_status)
    app.router.add_post("/api/expense", handle_expense)
    app.router.add_post("/api/income", handle_income)
    app.router.add_get("/api/balance", handle_balance)
    app.router.add_get("/api/report", handle_report)
    return app


def main() -> None:
    settings = load_settings()
    app = create_app()
    web.run_app(app, host=settings.webapp_host, port=settings.webapp_port)


if __name__ == "__main__":
    main()
