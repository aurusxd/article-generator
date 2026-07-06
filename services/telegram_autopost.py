import os
import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from services.image_service import IMAGE_FOLDER
from services.logger import log
from utils.other import extract_photo_description, sanitize_html,truncate_text


class TelegramPostService:
    def __init__(self, bot: Bot, channel_id: str):
        self.bot = bot
        self.channel_id = channel_id

    async def publish_article(
        self,
        text: str,
        with_photo: bool,
    ) -> bool:
        try:
            text_post = sanitize_html(text)
            post_text = f"{text_post}"
            
            if with_photo:
                image_path=os.path.join(IMAGE_FOLDER, f"img_{int(time.time())}.jpg")
                clean_text = extract_photo_description(post_text)
                lines = clean_text.strip().split("\n")
                caption_raw = "\n".join(lines[:2]) if len(lines) > 1 else lines[0]
                caption = truncate_text(sanitize_html(caption_raw.strip()), 1024)
                with open(image_path, "rb") as img:
                    self.bot.send_photo(
                        self.channel_id,
                        photo=img,
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