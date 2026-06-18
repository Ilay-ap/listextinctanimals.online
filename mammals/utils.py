from django.utils.translation import get_language

def get_normalized_lang_code() -> str:
    """Return the normalized language code (e.g., 'pt', 'en')"""
    current_lang: str | None = get_language()
    return current_lang.split('-')[0] if current_lang else 'pt'
