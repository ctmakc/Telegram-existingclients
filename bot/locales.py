translations = {
    "en": {
        "greeting": "Hello!",
        "farewell": "Goodbye!"
    },
    "ru": {
        "greeting": "Привет!",
        "farewell": "До свидания!"
    },
    "es": {
        "greeting": "¡Hola!",
        "farewell": "¡Adiós!"
    }
}

def get_translation(lang_code, message_key):
    return translations.get(lang_code, {}).get(message_key, "Translation not found")