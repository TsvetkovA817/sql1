import json
import os
from config_handler import ConfigHandler


class LanguageHandler:
    def __init__(self):
        self.config = ConfigHandler()
        self.current_lang = self.config.get_language()
        self.translations = self._load_translations()

    def _load_translations(self):
        """Загружает переводы из JSON-файлов"""
        translations = {}
        lang_files = {
            'ru': 'lang/ru.json',
            'en': 'lang/en.json',
            'zh': 'lang/zh.json'
        }

        for lang, file_path in lang_files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations[lang] = json.load(f)
            except FileNotFoundError:
                print(f"Warning: Language file not found - {file_path}")
                translations[lang] = {}

        return translations

    def set_language(self, lang_code):
        """Устанавливает текущий язык"""
        if lang_code in self.translations:
            self.current_lang = lang_code
            self.config.update_language(lang_code)
        else:
            print(f"Warning: Language not supported - {lang_code}")

    def get_text(self, text_id, default_text=None):
        """Возвращает перевод для указанного ID"""
        lang_data = self.translations.get(self.current_lang, {})
        return lang_data.get(text_id, default_text or f"[{text_id}]")

    def get_supported_languages(self):
        """Возвращает список поддерживаемых языков"""
        return list(self.translations.keys())
