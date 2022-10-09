import json


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


class LocalizationService:
    """
    The localization service provides a way to localize strings.
    Localized strings are stored in JSON files in the res/lang directory.
    Each file should be named after the language code (ISO 639-1 standard
    with an optional ISO 3166-1 alpha-2 country code).  For example: en, en-US, fr, fr-CA, de, de-DE, etc.

    The JSON file should be a dictionary of key/value pairs.  The keys should be the string to localize,
    and the values should be the localized string.  For example:
    {
        "Hello": "Bonjour",
        "Goodbye": "Au revoir"
    }
    """

    _instance = None

    warn_on_missing: bool = True
    """Whether to print a warning when a string is missing."""

    throw_on_missing: bool = False
    """
    Whether to throw an exception when a string is missing. This is useful for testing and
    checking the stack trace to see where the missing string is.
    """

    def __init__(self):
        """
        Initializes the LocalizationService class.
        """
        self._strings: dict[str, str] = {}
        self._locale: str = "en"
        self._fallback_locale: str = "en"
        self._warned_strings: set[str] = set()
        self._loadStrings()

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

    def set_locale(self, locale: str, fallback_locale: str = "en"):
        """
        Sets the locale. The language code should be in the format of
        the ISO 639-1 standard, with an optional ISO 3166-1 alpha-2 country code.
        For example: en, en-US, fr, fr-CA, de, de-DE, etc.

        If you are testing the application for missing strings, you can set the
        fallback locale to None. This will cause the application to throw an
        exception when a string is missing. By default, the fallback locale is "en".

        Args:
            locale (str): The language code to set.
            fallback_locale (str, optional): The fallback language code to use. Defaults to "en".
        """
        self._locale = locale
        self._fallback_locale = fallback_locale
        self._loadStrings()

    def _loadStrings(self):
        """
        Loads the strings.
        """
        self._strings = {}
        self._warned_strings = set()
        self._loadStringsForLocale(self._locale)
        if self._fallback_locale:
            self._loadStringsForLocale(self._fallback_locale)

    def _loadStringsForLocale(self, locale: str):
        """
        Loads the strings for the given locale.

        Args:
            locale (str): The locale.
        """
        try:
            with open("res/lang/" + locale + ".json", "r") as file:
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
            self._warnMissingString(key_or_string)

        return result.format(**kwargs)

    def _warnMissingString(self, key: str):
        """
        Warns that a string is missing.

        Args:
            key (str): The key of the missing string.
        """
        if self.throw_on_missing:
            raise Exception("Missing string: " + key)

        if self.warn_on_missing and key not in self._warned_strings:
            print("Missing string: " + key)
            self._warned_strings.add(key)
