
from datetime import time
import os

from yandex_cloud_ml_sdk import YCloudML
IMAGE_FOLDER = "generated_images"

class ImageService:
    def generate_image(description: str):
        try:
            sdk = YCloudML(
                folder_id=os.getenv('YANDEX_FOLDER_ID'),
                auth=os.getenv('YANDEX_API_KEY')
            )
            model = sdk.models.image_generation("yandex-art").configure(width_ratio=1, height_ratio=1)
            image_path = os.path.join(IMAGE_FOLDER, f"img_{int(time.time())}.jpg")
            operation = model.run_deferred([description])
            result = operation.wait()

            with open(image_path, "wb") as f:
                f.write(result.image_bytes)

            return image_path
        except Exception as e:
            print(f"❌ Ошибка генерации изображения: {e}")
            return None