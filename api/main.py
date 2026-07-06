from fastapi import FastAPI
from pydantic import BaseModel

from services.deepseek_service import ask_agent

app = FastAPI()

class RequestData(BaseModel):
    topic: str
    description: str
    with_photo: bool

@app.post("/ask")
async def ask(data: RequestData):
    """Обрабатывает ввод пользователя через ИИ-агента и возвращает результат."""
    result = await ask_agent(
        user_topic=data.topic,
        description=data.description,
        with_photo=data.with_photo
    )

    return {
        "answer": result
    }
