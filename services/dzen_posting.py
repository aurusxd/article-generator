from services.dzen_service import DzenPostService, dzen_post_service


async def save_dzen_article(
    title: str,
    description: str,
    image_path: str | None = None,
) -> bool:
    return await dzen_post_service.save_article(
        title=title,
        description=description,
        image_path=image_path,
    )


async def save_dzen_article_from_text(
    text: str,
    image_path: str | None = None,
) -> bool:
    return await dzen_post_service.save_article_from_text(
        text=text,
        image_path=image_path,
    )


