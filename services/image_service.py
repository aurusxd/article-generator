import asyncio
import base64
import os
import time
from pathlib import Path

from openai import AsyncOpenAI
import requests

from services.logger import log


IMAGE_FOLDER = "generated_images"
XAI_BASE_URL = "https://api.x.ai/v1"
CLOUDFLARE_BASE_URL = "https://api.cloudflare.com/client/v4"


class ImageService:
    async def generate_image(self, description: str) -> str | None:
        log.info(f"Запущена генерация изображения: {description}")

        provider = os.getenv("IMAGE_PROVIDER", "cloudflare").lower()
        if provider == "cloudflare":
            return await self._generate_cloudflare(description)
        if provider == "xai":
            return await self._generate_xai(description)

        log.error(f"Неизвестный провайдер изображений: {provider}")
        return None

    async def _generate_cloudflare(self, description: str) -> str | None:
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not account_id or not api_token:
            log.error("Не заданы CLOUDFLARE_ACCOUNT_ID или CLOUDFLARE_API_TOKEN")
            return None

        model = os.getenv(
            "CLOUDFLARE_IMAGE_MODEL",
            "@cf/black-forest-labs/flux-1-schnell",
        )
        url = f"{CLOUDFLARE_BASE_URL}/accounts/{account_id}/ai/run/{model}"

        def request_image() -> bytes:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_token}"},
                json={
                    "prompt": description[:2048],
                    "steps": int(os.getenv("CLOUDFLARE_IMAGE_STEPS", "4")),
                },
                timeout=90,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload.get("success", False):
                raise RuntimeError(f"Cloudflare API error: {payload.get('errors')}")

            encoded_image = (payload.get("result") or {}).get("image")
            if not encoded_image:
                raise ValueError("Cloudflare API не вернул изображение")
            return base64.b64decode(encoded_image)

        try:
            Path(IMAGE_FOLDER).mkdir(parents=True, exist_ok=True)
            image_data = await asyncio.to_thread(request_image)
            image_path = Path(IMAGE_FOLDER) / f"img_{time.time_ns()}.jpg"
            image_path.write_bytes(image_data)
            log.success(f"Изображение сохранено: {image_path} (Cloudflare Workers AI)")
            return str(image_path)
        except Exception:
            log.exception("Ошибка генерации изображения через Cloudflare Workers AI")
            return None

    async def _generate_xai(self, description: str) -> str | None:
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
