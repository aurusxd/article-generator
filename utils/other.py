import html
import re
from html.parser import HTMLParser


def sanitize_html(text: str) -> str:
    """Converts generated HTML to tags supported by Telegram."""

    class TelegramHTMLSanitizer(HTMLParser):
        tag_map = {
            "h1": "b",
            "h2": "b",
            "h3": "b",
            "h4": "b",
            "h5": "b",
            "h6": "b",
            "strong": "b",
            "em": "i",
            "ins": "u",
            "strike": "s",
            "del": "s",
        }
        allowed_tags = {"b", "i", "u", "s", "a", "code", "pre", "blockquote"}
        line_break_tags = {"br", "hr"}
        block_tags = {"p", "div"}

        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.parts = []
            self.stack = []

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()

            if tag in self.line_break_tags:
                self.parts.append("\n")
                return

            if tag in self.block_tags:
                return

            mapped_tag = self.tag_map.get(tag, tag)
            if mapped_tag not in self.allowed_tags:
                return

            if mapped_tag == "a":
                href = next((value for name, value in attrs if name.lower() == "href"), None)
                if not href:
                    return
                self.parts.append(f'<a href="{html.escape(href, quote=True)}">')
            else:
                self.parts.append(f"<{mapped_tag}>")

            self.stack.append(mapped_tag)

        def handle_endtag(self, tag):
            tag = tag.lower()

            if tag in self.block_tags:
                self.parts.append("\n")

            mapped_tag = self.tag_map.get(tag, tag)
            if mapped_tag not in self.allowed_tags or mapped_tag not in self.stack:
                return

            while self.stack:
                open_tag = self.stack.pop()
                self.parts.append(f"</{open_tag}>")
                if open_tag == mapped_tag:
                    break

            if tag in self.tag_map and mapped_tag == "b":
                self.parts.append("\n")

        def handle_data(self, data):
            self.parts.append(html.escape(data, quote=False))

        def handle_entityref(self, name):
            self.parts.append(f"&{name};")

        def handle_charref(self, name):
            self.parts.append(f"&#{name};")

        def get_html(self):
            while self.stack:
                self.parts.append(f"</{self.stack.pop()}>")
            return "".join(self.parts).strip()

    parser = TelegramHTMLSanitizer()
    parser.feed(text or "")
    parser.close()
    return parser.get_html()


def extract_photo_description(text: str):
    match = re.search(r'\[ФОТО:(.*?)\]', text, re.DOTALL)
    if not match:
        return None, text
    desc = match.group(1).strip()
    cleaned_text = text.replace(match.group(0), "").strip()
    return desc, cleaned_text


def truncate_text(text: str, limit: int = 1024) -> str:
    return text if len(text) <= limit else text[:limit - 3] + "..."

def remove_html_tags(text):
    # Компилируем шаблон для поиска тегов и заменяем их на пустую строку
    clean_pattern = re.compile(r'<.*?>')
    return re.sub(clean_pattern, '', text)
