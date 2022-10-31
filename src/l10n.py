from dataclasses import dataclass
import json
import logging


def __(key_or_string: str, **kwargs) -> str:
    """
    Gets the localized string for the given key or string.

    Args:
        key_or_string (str): The key or string to localize.
        **kwargs: The keyword arguments to use when formatting the string.

    Returns:
        str: The localized string.
    """
    return LocalizationService.instance().get(key_or_string, **kwargs)


@dataclass
class Language:
    """
    Represents a language.

    Attributes:
        code (str): The language code.
        name (str): The language name.
    """

    code: str
    name: str


class LocalizationService:
    """
    The localization service provides a way to localize strings.
    Localized strings are stored in JSON files in the "res/lang/" directory.
    Each file should be named after the ISO 639-1 language code with an
    optional ISO 3166-1 alpha-2 country code.
    For example: "en.json", "en-US.json", "fr.json", "fr-CA.json", "de.json", "de-DE.json", etc.

    The JSON file should be a dictionary of key/value pairs.  The keys should be the string to localize,
    and the values should be the localized string. Nested dictionaries are also supported.
    You can mix and match nested dictionaries with regular key/value pairs. For example:

    {
        "Hello, how are you?": "Bonjour, comment allez-vous?",
        "Okay": "D'accord",
        "Cancel": "Annuler",
        "{count} of {total} items selected": "{count} sur {total} éléments sélectionnés"
        "menu_options": {
            "new_game": "Nouvelle partie",
            "load_game": "Charger une partie",
            "options": "Options",
            "quit": "Quitter"
            "score": "Votre score est de {score} points."
        },
        "Are you sure you want to quit?": "Êtes-vous sûr de vouloir quitter?"
        "Select difficulty": "Sélectionnez la difficulté"
    }

    To localize a string, use the __() helper function. For example:

    print(__("Hello, how are you?"))
    print(__("{count} of {total} items selected", count=5, total=10))
    print(__("menu_options.new_game"))
    print(__("menu_options.score", score=100))

    Will print:

    Bonjour, comment allez-vous?
    5 sur 10 éléments sélectionnés
    Nouvelle partie
    Votre score est de 100 points.

    Languages need to be registered in the "languages.json" file. For example:

    {
        "fallback_lang": "en",
        "langs": [
            {
                "code": "en",
                "name": "English",
            },
            {
                "code": "fr",
                "name": "Français",
            }
        ]
    }
    """

    _instance = None

    warn_on_missing: bool = True
    """
    Whether to print a warning when a string is missing.
    """

    throw_on_missing: bool = False
    """
    Whether to throw an exception when a string is missing. This is useful for testing and
    checking the stack trace to see where the missing string is.
    """

    ignore_fallback: bool = False
    """
    Whether to ignore the fallback locale. If you set this to true, the fallback locale will not be loaded.
    This can be useful if you want to test for missing strings in a specific language.
    """

    def __init__(self):
        """
        Initializes the LocalizationService class.
        """
        self._strings: dict[str, str] = {}
        self._locale: str = "en"
        self._fallback_locale: str = "en"
        self._warned_strings: set[str] = set()
        self._languages: list[Language] = []
        self._load_languages()
        self._load_strings()

    @staticmethod
    def instance() -> "LocalizationService":
        """
        Gets the instance of the localization service.

        Returns:
            LocalizationService: The instance of the localization service.
        """
        if not LocalizationService._instance:
            LocalizationService._instance = LocalizationService()

        return LocalizationService._instance

    def set_locale(self, locale: str):
        """
        Sets the locale. The language code should be in the format of
        the ISO 639-1 standard, with an optional ISO 3166-1 alpha-2 country code.
        For example: en, en-US, fr, fr-CA, de, de-DE, etc.

        Args:
            locale (str): The language code to set.
            fallback_locale (str, optional): The fallback language code to use. Defaults to "en".
        """
        self._locale = locale
        self._load_strings()

    def _load_strings(self):
        """
        Loads the strings.
        """
        self._strings = {}
        self._warned_strings = set()
        if self._fallback_locale and self._locale != self._fallback_locale and not self.ignore_fallback:
            self._load_strings_for_locale(self._fallback_locale)
        self._load_strings_for_locale(self._locale)

    def _load_strings_for_locale(self, locale: str):
        """
        Loads the strings for the given locale.

        Args:
            locale (str): The locale.
        """
        try:
            with open("res/lang/" + locale + ".json", "r", encoding="utf-8") as file:
                data = json.load(file)
                self._strings.update(self._flatten(data))
        except FileNotFoundError:
            pass

    def _flatten(self, data: dict, prefix: str = ""):
        """
        Flattens the given dictionary.

        Args:
            data (dict): The dictionary to flatten.
            prefix (str, optional): The prefix to use. Defaults to "".

        Returns:
            dict: The flattened dictionary.
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result.update(self._flatten(value, prefix + key + "."))
            else:
                result[prefix + key] = value

        return result

    def get_language(self) -> str:
        """
        Gets the language.

        Returns:
            str: The language.
        """
        return self._locale

    def get(self, key_or_string: str, **kwargs) -> str:
        """
        Gets the localized string for the given key or string.

        Args:
            key_or_string (str): The key or string to localize.
            **kwargs: The keyword arguments to use when formatting the string.

        Returns:
            str: The localized string.
        """
        if key_or_string in self._strings:
            result = self._strings[key_or_string]
        else:
            result = key_or_string
            self._warn_missing_string(key_or_string)

        return result.format(**kwargs)

    def _warn_missing_string(self, key: str):
        """
        Warns that a string is missing.

        Args:
            key (str): The key of the missing string.
        """
        if self.throw_on_missing:
            raise Exception("Missing string: " + key)

        if self.warn_on_missing and key not in self._warned_strings:
            logging.warn("Missing string: " + key)
            self._warned_strings.add(key)

    def _load_languages(self):
        """
        Loads the languages.
        """
        with open("res/lang/languages.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            self._fallback_locale = data["fallback_lang"]
            self._languages = [Language(**lang) for lang in data["langs"]]

    def get_languages(self) -> list[Language]:
        """
        Gets the languages.

        Returns:
            list[Language]: The languages.
        """
        return self._languages

    def get_fallback_language(self) -> str:
        """
        Gets the fallback language.

        Returns:
            str: The fallback language as a ISO 639-1 language code.
        """
        return self._fallback_locale
