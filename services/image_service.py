
import os
import time
from pathlib import Path
from services.logger import log
from yandex_ai_studio_sdk import AsyncAIStudio
IMAGE_FOLDER = "generated_images"

class ImageService:
    async def generate_image(self,description: str):
        log.info(f"зашел в generate_image: {description}")
        try:
            Path(IMAGE_FOLDER).mkdir(parents=True, exist_ok=True)
            sdk = AsyncAIStudio(
                folder_id=os.getenv('YANDEX_FOLDER_ID'),
                auth=os.getenv('YANDEX_API_KEY')
            )
            model = sdk.models.image_generation("yandex-art").configure(width_ratio=1, height_ratio=1)
            image_path = os.path.join(IMAGE_FOLDER, f"img_{int(time.time())}.jpg")
            operation = await model.run_deferred([description])
            result = await operation.wait()

            with open(image_path, "wb") as f:
                f.write(result.image_bytes)

            log.success("Сгенерировал изображение ")
            return image_path
        except Exception as e:
            log.error(f"❌ Ошибка генерации изображения: {e}")
            return None
        
image_service = ImageService()
