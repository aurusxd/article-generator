import re



def sanitize_html(text: str) -> str:
    """Преобразует нестандартные HTML-теги в допустимые для Telegram"""
    text = re.sub(r'</?(h1|h2|h3|h4|h5|h6)>', '<b>', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</?(div|span|p)>', '', text)
    return text

def extract_photo_description(text: str):
    match = re.search(r'\[ФОТО:(.*?)\]', text, re.DOTALL)
    if not match:
        return None, text
    desc = match.group(1).strip()
    cleaned_text = text.replace(match.group(0), "").strip()
    return desc, cleaned_text