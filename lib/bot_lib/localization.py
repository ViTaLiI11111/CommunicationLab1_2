import yaml
from pathlib import Path

class Localization:
    def __init__(self, locales_path="config/locales.yml"):
        self.messages = {}
        self._load_locales(locales_path)
        self.default_lang = 'en'

    def _load_locales(self, locales_path):
        try:
            project_root = Path(__file__).parent.parent.parent
            filepath = project_root / locales_path
            with open(filepath, 'r', encoding='utf-8') as f:
                self.messages = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Locales file not found at {filepath}")
            self.messages = {}
        except yaml.YAMLError as e:
            print(f"Error parsing locales file: {e}")
            self.messages = {}

    def get_message(self, key, lang='en'):
        lang_messages = self.messages.get(lang, self.messages.get(self.default_lang, {}))
        return lang_messages.get(key, f"_[{key}]_")