import asyncio
import logging

from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.bot import build_dispatcher, create_bot
from app.config import load_settings


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    bot = create_bot(settings.bot_token)
    if settings.webapp_url:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Open",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            )
        except Exception as exc:  # pragma: no cover - best effort
            logging.getLogger(__name__).warning(
                "Failed to set web app menu button: %s", exc
            )
    dp = build_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
