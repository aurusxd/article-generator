import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest

import services.dzen_service as dzen_service_module
from services.dzen_service import DzenPostService, html_to_text, split_title_and_description


class FakePlaywright:
    def __init__(self) -> None:
        self.page = Mock(name="page")
        self.context = Mock(name="context")
        self.context.new_page = AsyncMock(return_value=self.page)
        self.context.close = AsyncMock()

        self.browser = Mock(name="browser")
        self.browser.new_context = AsyncMock(return_value=self.context)
        self.browser.close = AsyncMock()

        self.chromium = Mock(name="chromium")
        self.chromium.launch = AsyncMock(return_value=self.browser)


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def disable_file_logging(monkeypatch):
    monkeypatch.setattr(dzen_service_module, "log", Mock())


def playwright_context(fake: FakePlaywright):
    @asynccontextmanager
    async def manager():
        yield fake

    return manager


def test_save_article_posts_text_and_closes_browser(tmp_path):
    state = tmp_path / "dzen_state.json"
    state.write_text("{}", encoding="utf-8")
    service = DzenPostService(str(state), headless=False)
    fake = FakePlaywright()

    service._open_article_editor = AsyncMock()
    service._fill_title = AsyncMock()
    service._fill_description = AsyncMock()
    service._fill_description_with_photo = AsyncMock()
    service._upload_image = AsyncMock()
    service._save_draft = AsyncMock()

    with patch("services.dzen_service.async_playwright", playwright_context(fake)):
        result = run(service.save_article(" Заголовок ", " Текст статьи "))

    assert result is True
    fake.chromium.launch.assert_awaited_once_with(headless=False)
    fake.browser.new_context.assert_awaited_once_with(storage_state=str(state))
    service._open_article_editor.assert_awaited_once_with(fake.page)
    service._fill_title.assert_awaited_once_with(fake.page, " Заголовок ")
    service._fill_description.assert_awaited_once_with(fake.page, " Текст статьи ")
    service._upload_image.assert_not_awaited()
    service._fill_description_with_photo.assert_not_awaited()
    service._save_draft.assert_awaited_once_with(fake.page)
    fake.context.close.assert_awaited_once()
    fake.browser.close.assert_awaited_once()


def test_save_article_posts_with_image(tmp_path):
    state = tmp_path / "dzen_state.json"
    state.write_text("{}", encoding="utf-8")
    image = tmp_path / "cover.png"
    image.write_bytes(b"image")
    service = DzenPostService(str(state))
    fake = FakePlaywright()

    service._open_article_editor = AsyncMock()
    service._fill_title = AsyncMock()
    service._fill_description = AsyncMock()
    service._upload_image = AsyncMock()
    service._fill_description_with_photo = AsyncMock()
    service._save_draft = AsyncMock()

    with patch("services.dzen_service.async_playwright", playwright_context(fake)):
        result = run(service.save_article("Заголовок", "Текст", str(image)))

    assert result is True
    service._upload_image.assert_awaited_once_with(fake.page, str(image))
    service._fill_description_with_photo.assert_awaited_once_with(fake.page, "Текст")
    service._fill_description.assert_not_awaited()
    service._save_draft.assert_awaited_once_with(fake.page)


def test_save_article_returns_false_without_authorized_session(tmp_path):
    service = DzenPostService(str(tmp_path / "missing-state.json"))

    with patch("services.dzen_service.async_playwright") as playwright:
        result = run(service.save_article("Заголовок", "Текст"))

    assert result is False
    playwright.assert_not_called()


def test_save_article_returns_false_and_cleans_up_after_posting_error(tmp_path):
    state = tmp_path / "dzen_state.json"
    state.write_text("{}", encoding="utf-8")
    service = DzenPostService(str(state))
    fake = FakePlaywright()
    service._open_article_editor = AsyncMock(side_effect=RuntimeError("Dzen is unavailable"))

    with patch("services.dzen_service.async_playwright", playwright_context(fake)):
        result = run(service.save_article("Заголовок", "Текст"))

    assert result is False
    fake.context.close.assert_awaited_once()
    fake.browser.close.assert_awaited_once()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("<p>Первый абзац</p><p>Второй<br>строка</p>", "Первый абзац\n\nВторой\nстрока"),
        ("Текст без разметки", "Текст без разметки"),
        ("", ""),
    ],
)
def test_html_to_text(source, expected):
    assert html_to_text(source) == expected


def test_save_article_from_text_extracts_h1_and_removes_html():
    service = DzenPostService()
    service.save_article = AsyncMock(return_value=True)

    result = run(
        service.save_article_from_text(
            "<h1>Заголовок <em>статьи</em></h1><p>Первый абзац.</p><p>Второй.</p>",
            image_path="cover.png",
        )
    )

    assert result is True
    service.save_article.assert_awaited_once_with(
        title="Заголовок статьи",
        description="Первый абзац.\n\nВторой.",
        image_path="cover.png",
    )


def test_split_title_and_description_uses_first_plain_text_line_as_title():
    title, description = split_title_and_description("Первая строка<br>Вторая строка")

    assert title == "Первая строка"
    assert description == "Вторая строка"


def test_close_help_popup_uses_stable_css_module_selector():
    service = DzenPostService()
    page = Mock()
    overlay = Mock()
    overlay.count = AsyncMock(return_value=1)
    overlay.wait_for = AsyncMock()
    page.locator.return_value.first = overlay
    service._click_first = AsyncMock(return_value=True)

    run(service._close_help_popup(page))

    selectors = service._click_first.await_args.args[1]
    assert '[class*="help-popup__closeCross"]' in selectors
    overlay.wait_for.assert_awaited_once_with(state="hidden", timeout=2000)


def test_fill_contenteditable_closes_delayed_help_popup_before_clicking():
    service = DzenPostService()
    page = Mock()
    page.keyboard.insert_text = AsyncMock()
    locator = Mock()
    locator.wait_for = AsyncMock()
    locator.click = AsyncMock()
    locator.press = AsyncMock()
    service._close_help_popup = AsyncMock()

    run(service._fill_contenteditable(page, locator, "Article title"))

    service._close_help_popup.assert_awaited_once_with(page)
    locator.click.assert_awaited_once()
    page.keyboard.insert_text.assert_awaited_once_with("Article title")
