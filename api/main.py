from fastapi import FastAPI
from pydantic import BaseModel

from services.deepseek_service import ask_agent

app = FastAPI()

class RequestData(BaseModel):
    topic: str

@app.post("/ask")
async def ask(data: RequestData):
    """Обрабатывает ввод пользователя через ИИ-агента и возвращает результат."""
    result = await ask_agent(
        user_topic=data.topic,
    )

    return {
        "answer": result
    }
