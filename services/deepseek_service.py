import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from services.tools.web_search import search_web
from utils.other import extract_photo_description
from services.logger import log
from services.image_service import image_service
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Ищет актуальную информацию в интернете",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос",
                    }
                },
                "required": ["query"],
            },
        },
    },
]
system_prompt ="""
Ты — профессиональный журналист, редактор и эксперт по теме, на которую пишешь статью.

Перед написанием сначала определи тематику статьи и выступай как специалист именно в этой области. Не упоминай, что ты ИИ.

Перед написанием оцени, требуются ли актуальные данные.

Запрещено использовать search_web для образовательных, исторических, обзорных и объясняющих статей.

Вызывай search_web исключительно в случаях, когда без него невозможно получить корректный ответ из-за необходимости использовать актуальные данные.

Правила написания:

- Пиши естественным человеческим языком.
- Не используй шаблонные ИИ-фразы вроде "В современном мире...", "Стоит отметить...", "Важно понимать...".
- Не повторяй одну мысль разными словами.
- Не выдумывай факты.
- Если информации недостаточно — используй search_web или прямо укажи, что достоверных данных недостаточно.
- Объясняй сложные термины простым языком.
- Делай небольшие абзацы.
- Структурируй статью логично.
- Не рекламируй компании, продукты или сервисы без необходимости.
- Не давай профессиональных (финансовых, медицинских, юридических и т.п.) рекомендаций как окончательную истину.
- Не используй Markdown.
- Не используй эмодзи.
- Выводи только готовую статью.
"""

available_tools = {
    "search_web": search_web,
}
def build_user_promt(topic: str,description: str,with_photo: bool):
    
    if(with_photo):
        return f"""
    Напиши качественную статью на тему: {topic} с HTML-разметкой (b, i, a, h1)
    Описание статьи: {description}

    Требования:
    - Заголовок.
    - Добавь описание изображения в формате [ФОТО: ...].
    - Интересное вступление.
    - Основная часть с логичными подзаголовками.
    - Заключение.

    Размер:
    не больше 1500 символов.

    Статья должна:

    - легко читаться;
    - удерживать внимание;
    - объяснять тему простыми словами;
    - содержать реальные примеры;
    - быть уникальной;
    - не содержать воды;
    - быть полностью готовой к публикации.

    В конце добавь краткий вывод.
    Пример:
    <h1>Как мышь спасла город</h1>
    <i>История, которую вы не слышали</i>
    [ФОТО: старая карта, на которой изображена мышь, сидящая на бочке с порохом в подвале замка]
    """
    else:
        return f"""
    Напиши качественную статью на тему: {topic} с HTML-разметкой (b, i, a, h1)
    Описание статьи: {description}

    Требования:

    - Заголовок.
    - Интересное вступление.
    - Основная часть с логичными подзаголовками.
    - Заключение.

    Размер:
    не больше 2500 символов.

    Статья должна:

    - легко читаться;
    - удерживать внимание;
    - объяснять тему простыми словами;
    - содержать реальные примеры;
    - быть уникальной;
    - не содержать воды;
    - быть полностью готовой к публикации.

    В конце добавь краткий вывод.
    Пример:
    <h1>Как мышь спасла город</h1>
    <i>История, которую вы не слышали</i>
    """


async def ask_agent(
    user_topic: str,
    description: str,
    with_photo: bool = False,
    return_image_path: bool = False,
):
    messages = [
        {
            "role": "system",
            "content": system_prompt

        },
        {
            "role": "user",
            "content": build_user_promt(user_topic,description,with_photo),
        },
    ]

    


    first_response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = first_response.choices[0].message

    async def prepare_article_photo(article_text: str):
        image_path = None

        if with_photo:
            photo_desc, clean_text = extract_photo_description(article_text)
            article_text = clean_text
            if not photo_desc:
                log.error("Photo description was not found. Sending text only.")
            else:
                image_path = await image_service.generate_image(description=photo_desc)
                if not image_path:
                    log.error("Image generation failed.")

        return article_text, image_path

    if not message.tool_calls:
        article_text, image_path = await prepare_article_photo(message.content)
        if return_image_path:
            return article_text, image_path
        return article_text

    messages.append(message)

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        tool_result = available_tools[function_name](**arguments)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result),
            }
        )

    result = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
    )


    article_text, image_path = await prepare_article_photo(result.choices[0].message.content)
    if return_image_path:
        return article_text, image_path

    return article_text


    
    

