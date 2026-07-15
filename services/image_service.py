import base64
import os
import time
from pathlib import Path

from openai import AsyncOpenAI

from services.logger import log


IMAGE_FOLDER = "generated_images"
XAI_BASE_URL = "https://api.x.ai/v1"


class ImageService:
    async def generate_image(self, description: str) -> str | None:
        log.info(f"Запущена генерация изображения: {description}")

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            log.error("Не задан XAI_API_KEY")
            return None

        try:
            Path(IMAGE_FOLDER).mkdir(parents=True, exist_ok=True)
            async with AsyncOpenAI(api_key=api_key, base_url=XAI_BASE_URL) as client:
                response = await client.images.generate(
                    model=os.getenv("XAI_IMAGE_MODEL", "grok-imagine-image-quality"),
                    prompt=description,
                    response_format="b64_json",
                    extra_body={
                        "aspect_ratio": os.getenv("XAI_IMAGE_ASPECT_RATIO", "1:1"),
                        "resolution": os.getenv("XAI_IMAGE_RESOLUTION", "1k"),
                    },
                )

            image_data = response.data[0].b64_json if response.data else None
            if not image_data:
                raise ValueError("xAI API не вернул данные изображения")

            image_path = Path(IMAGE_FOLDER) / f"img_{time.time_ns()}.jpg"
            image_path.write_bytes(base64.b64decode(image_data))

            log.success(f"Изображение сохранено: {image_path}")
            return str(image_path)
        except Exception:
            log.exception("Ошибка генерации изображения через xAI API")
            return None


image_service = ImageService()
