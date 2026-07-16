from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile

from services.logger import log
from utils.other import extract_photo_description, sanitize_html, truncate_html


class TelegramPostService:
    def __init__(self, bot: Bot, channel_id: str):
        self.bot = bot
        self.channel_id = channel_id

    async def publish_article(
        self,
        text: str,
        with_photo: bool,
        image_path: str | None = None,
    ) -> bool:
        try:
            text_post = sanitize_html(text)
            post_text = f"{text_post}"
            
            if with_photo and image_path:
                _, clean_text = extract_photo_description(post_text)
                caption = truncate_html(sanitize_html(clean_text.strip()), 1024)
                await self.bot.send_photo(
                    self.channel_id,
                    photo=FSInputFile(image_path),
                    caption=caption,
                    parse_mode="HTML"
                )
                log.info(f"Статья с фото опубликована в Telegram: {text}")
                return True
                

            await self.bot.send_message(
                chat_id=self.channel_id,
                text=post_text,
                disable_web_page_preview=True,
                parse_mode="HTML"
            )

            log.info(f"Статья без фото опубликована в Telegram: {text}")
            return True

        except TelegramAPIError:
            log.exception("Ошибка при публикации статьи в Telegram")
            return False
