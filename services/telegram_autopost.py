from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from services.logger import log
from utils.other import sanitize_html


class TelegramPostService:
    def __init__(self, bot: Bot, channel_id: str):
        self.bot = bot
        self.channel_id = channel_id

    async def publish_article(
        self,
        text: str,
    ) -> bool:
        try:
            text_post = sanitize_html(text)
            post_text = f"{text_post}"
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=post_text,
                disable_web_page_preview=True,
            )

            log.info(f"Статья опубликована в Telegram: {text}")
            return True

        except TelegramAPIError:
            log.exception("Ошибка при публикации статьи в Telegram")
            return False