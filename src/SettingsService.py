import json


class SettingsService:
    """
    The settings services provides a simple way for storing key/value pairs in a "settings.json".
    """

    _instance = None

    _settings_file = "settings.json"

    @staticmethod
    def instance() -> "SettingsService":
        """
        Gets the instance of the SettingsService.

        Returns:
            SettingsService: The instance.
        """
        if not SettingsService._instance:
            SettingsService._instance = SettingsService()
        return SettingsService._instance

    def __init__(self):
        """
        Creates a new instance of the SettingsService.
        """
        self._settings = {}
        self._load_settings()

    def _load_settings(self):
        """
        Loads the settings.
        """
        try:
            with open(self._settings_file, "r") as file:
                self._settings = json.load(file)
        except FileNotFoundError:
            pass

    def _save_settings(self):
        """
        Saves the settings.
        """
        with open(self._settings_file, "w") as file:
            json.dump(self._settings, file, indent=4)

    def get(self, key: str, default_value=None):
        """
        Gets the value for the given key.

        Args:
            key (str): The key.
            default_value (any, optional): The default value to use if the key is not found. Defaults to None.

        Returns:
            any: The value.
        """
        return self._settings.get(key, default_value)

    def set(self, key: str, value):
        """
        Sets the value for the given key.

        Args:
            key (str): The key.
            value (any): The value.
        """
        self._settings[key] = value
        self._save_settings()
