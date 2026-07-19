import os
import re
from html.parser import HTMLParser
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from services.logger import log
from utils.other import remove_html_tags


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_text(text: str) -> str:
    parser = _TextExtractor()
    parser.feed(text or "")
    parser.close()
    return parser.get_text()


def split_title_and_description(text: str, fallback_title: str = "Новая статья") -> tuple[str, str]:
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", text or "", re.IGNORECASE | re.DOTALL)
    if title_match:
        title = html_to_text(title_match.group(1)).strip()
        description = re.sub(
            r"<h1[^>]*>.*?</h1>",
            "",
            text or "",
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return title or fallback_title, html_to_text(description)

    plain_text = html_to_text(text or "")
    lines = [line.strip() for line in plain_text.splitlines() if line.strip()]
    if not lines:
        return fallback_title, ""

    return lines[0], "\n\n".join(lines[1:]).strip()


class DzenPostService:
    def __init__(
        self,
        storage_state_path: str = "/app/dzen_state.json",
        headless: bool = True,
    ):
        self.storage_state_path = storage_state_path
        self.headless = headless

    async def save_article(
        self,
        title: str,
        description: str,
        image_path: str | None = None,
    ) -> bool:
        try:
            if not Path(self.storage_state_path).exists():
                log.error(f"Dzen storage state not found: {self.storage_state_path}")
                return False

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(storage_state=self.storage_state_path)
                page = await context.new_page()

                try:
                    await self._open_article_editor(page)

                    await self._fill_title(page, title)
                    if image_path:
                        await self._upload_image(page, image_path)
                        await self._fill_description_with_photo(page, description)

                    else:
                        await self._fill_description(page, description)
                    await self._save_draft(page)

                    log.info(f"Dzen draft saved. Title: {title}")
                    return True
                finally:
                    await context.close()
                    await browser.close()

        except Exception:
            log.exception("Dzen autoposting failed")
            return False

    async def save_article_from_text(
        self,
        text: str,
        image_path: str | None = None,
    ) -> bool:
        title, description = split_title_and_description(text)
        return await self.save_article(
            title=remove_html_tags(title),
            description=remove_html_tags(description),
            image_path=image_path,
        )

    async def _open_article_editor(self, page: Page) -> None:
        await page.goto("https://dzen.ru", wait_until="domcontentloaded")

        await self._click_first(
            page,
            [
                '[data-stub="32"]',
                '[data-testid="profile-button"]',
                'button[aria-label*="рофил"]',
            ],
            timeout=10000,
        )
        await self._click_first(
            page,
            [
                '[data-testid="create-button"]',
                'button:has-text("Создать")',
            ],
            timeout=10000,
        )
        await self._click_first(
            page,
            [
                '[data-testid="profile-menu-create-article"]',
                'text=Статья',
                'text=Написать статью',
            ],
            timeout=10000,
        )

        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1500)
        await self._close_help_popup(page)

    async def _upload_image(self, page: Page, image_path: str) -> None:
        image = Path(image_path)

        if not image.exists():
            print(f"Файл не существует: {image_path}")
            return

        # Открываем модальное окно
        await self._click_first(
            page,
            [
                'button[data-tip="Вставить изображение"]',
                'button:has(svg use[href*="add_gallery"])',
                'button:has(svg use[xlink\\:href*="add_gallery"])',
                '.article-editor-desktop--side-button__sideButton-1z',
            ],
            timeout=10000,
        )

        await page.get_by_role(
            "button",
            name="Загрузите файл",
            exact=True,
        ).wait_for(state="visible", timeout=10000)

        # Ищем input после открытия модального окна
        file_input = page.locator('input[type="file"]').last

        if await file_input.count() > 0:
            await file_input.set_input_files(str(image.resolve()))
            print(f"Изображение загружено: {image.resolve()}")
            return

        # Если input отсутствует — используем file chooser
        upload_button = page.get_by_role(
            "button",
            name="Загрузите файл",
            exact=True,
        )

        async with page.expect_file_chooser(timeout=10000) as chooser_info:
            await upload_button.click()

        chooser = await chooser_info.value
        await chooser.set_files(str(image.resolve()))

    async def _fill_title(self, page: Page, title: str) -> None:
        title = title.strip()
        await self._fill_contenteditable(
            page,
            page.locator(
                '.article-editor-desktop--editor__titleInput-2D '
                '[contenteditable="true"][role="textbox"]'
            ).first,
            title,
        )

    async def _fill_description_with_photo(self, page: Page, description: str) -> None:
        editors = page.locator(
            '.public-DraftEditor-content'
            '[contenteditable="true"]:visible'
        )

        count = await editors.count()
        print("Редакторов найдено:", count)

        if count == 0:
            raise RuntimeError("Редакторы Draft.js не найдены")

        # Пока выбираем второй редактор
        editor = editors.nth(0)

        # Внутренний абзац Draft.js
        blocks = editor.locator('div[data-block="true"]')

        if await blocks.count() > 0:
            target = blocks.last
        else:
            target = editor

        await target.scroll_into_view_if_needed()

        # Проверяем, что фокус действительно внутри нужного редактора
        focused = await editor.evaluate("""
            el => el === document.activeElement
                || el.contains(document.activeElement)
        """)

        log.info("Фокус внутри выбранного редактора:", focused)

        await page.keyboard.insert_text(description)

        await page.wait_for_timeout(1000)


    async def _fill_description(self, page: Page, description: str) -> None:
        description = description.strip()
        editor = page.locator('[aria-describedby="placeholder-ZenDraftEditor"]').first
        if await editor.count() == 0:
            contenteditable = page.locator('[contenteditable="true"][role="textbox"]')
            if await contenteditable.count() > 1:
                editor = contenteditable.nth(1)

        await self._fill_contenteditable(page, editor, description)

    async def _save_draft(self, page: Page) -> None:
        clicked = await self._click_first(
                    page,
                    [
                        '[data-testid*="save"]',
                        'button:has-text("Опубликовать")',
                        'button:has-text("Черновик")',
                        'text=Сохранить',
                    ],
                    timeout=5000,
                    required=False,
                )

        if clicked:
            await page.wait_for_timeout(2000)
        else:
                # Dzen editor usually autosaves drafts. Wait a little to let it finish.
            await page.wait_for_timeout(5000)
            
            publish_button = page.locator('[data-testid="publish-btn"]')

            await publish_button.wait_for(state="visible", timeout=10000)

            await publish_button.click(timeout=10000)
            log.success("Финальная кнопка публикации нажата")

    async def _click_first(
        self,
        page: Page,
        selectors: list[str],
        timeout: int = 5000,
        required: bool = True,
    ) -> bool:
        for selector in selectors:
            try:
                await page.locator(selector).first.click(timeout=timeout)
                return True
            except PlaywrightTimeoutError:
                continue

        if required:
            raise RuntimeError(f"Could not click any selector: {selectors}")
        return False

    async def _close_help_popup(self, page: Page) -> None:
        await self._click_first(
            page,
            [
                '.article-editor-desktop--help-popup__closeCross-Lj',
                '[role="dialog"] [aria-label="Закрыть"]',
                '[aria-label="Закрыть"]',
            ],
            timeout=2000,
            required=False,
        )

    async def _fill_contenteditable(self, page: Page, locator, value: str) -> None:
        await locator.wait_for(state="visible", timeout=7000)
        await locator.click()
        await locator.press("Control+A")
        await locator.press("Backspace")
        await page.keyboard.insert_text(value)

    async def _fill_first(
        self,
        page: Page,
        selectors: list[str],
        value: str,
        timeout: int = 5000,
    ) -> None:
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.click()
                await locator.fill(value)
                return
            except PlaywrightTimeoutError:
                continue
            except Exception:
                try:
                    await locator.click()
                    await page.keyboard.insert_text(value)
                    return
                except Exception:
                    continue

        raise RuntimeError(f"Could not fill any selector: {selectors}")


dzen_post_service = DzenPostService(
    storage_state_path=os.getenv("DZEN_STORAGE_STATE_PATH", "./dzen_state.json"),
    headless=os.getenv("DZEN_HEADLESS", "true").lower() == "true",
)
