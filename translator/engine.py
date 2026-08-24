import requests.sessions
from deep_translator import GoogleTranslator

# deep-translator's requests call gets requests' default User-Agent
# ("python-requests/x.x"), which Google's scrape target silently serves
# a resultless page for. Patch in a browser UA so translations resolve.
_original_default_headers = requests.sessions.default_headers
requests.sessions.default_headers = lambda: {
    **_original_default_headers(),
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}


def translate(text: str, source_lang: str, target_lang: str) -> str:
    return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
