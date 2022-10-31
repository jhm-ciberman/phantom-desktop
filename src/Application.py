import sys
import logging

from PySide6 import QtCore, QtGui, QtWidgets

from .ModelsDownloader import ModelsDownloader

from .ProjectManager import ProjectManager
from .Workspace import Workspace
from .l10n import LocalizationService
from .SettingsService import SettingsService
from . import constants


class Application(QtWidgets.QApplication):
    """
    This class is a singleton that represents the application.
    """

    _instance = None

    @staticmethod
    def instance() -> "Application":
        """
        Returns the application instance.
        """
        if Application._instance is None:
            raise Exception("Application instance not created yet")
        return Application._instance

    @staticmethod
    def workspace() -> Workspace:
        """
        Returns the Workspace instance.
        """
        # Workspace is not a singleton because this will enable
        # in a future to have multiple projects open at the same time.
        return Application.instance()._workspace

    @staticmethod
    def projectManager() -> "ProjectManager":
        """
        Returns the project manager.
        """
        return Application.instance()._projectManager

    def __init__(self, args):
        """
        Initializes a new instance of the Application class.
        """
        super().__init__(args)
        if Application._instance is not None:
            raise Exception("Application instance already created")

        Application._instance = self

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(constants.app_log_file),
                logging.StreamHandler()
            ]
        )

        sys.excepthook = self._handleException

        self._modelsDownloader = ModelsDownloader(
            models_zip_url=constants.models_zip_url,
            release_tag=constants.models_release_tag,
            local_models_folder=constants.models_local_folder,
        )

        self.initLanguage()

        self.setApplicationVersion(constants.app_version)
        self.setApplicationName(constants.app_name)

        self._icon = QtGui.QIcon("res/img/icon.png")
        self.setWindowIcon(self._icon)

        self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

        p = self.palette()
        p.setColor(QtGui.QPalette.Window, QtCore.Qt.white)
        self.setPalette(p)

        self.setStyleSheet("""
            QStatusBar { background-color: #f0f0f0; }
        """)

        from .ImageProcessorService import \
            ImageProcessorService  # Avoid circular imports
        self._imageProcessorService = ImageProcessorService()
        self._workspace = Workspace(self._imageProcessorService)
        self._projectManager = ProjectManager(self._workspace)

    def _handleException(self, exctype, value, traceback):
        """
        Handles unhandled exceptions.
        """
        logging.error("Unhandled exception", exc_info=(exctype, value, traceback))
        QtWidgets.QMessageBox.critical(None, "Unhandled exception", str(value))

    def exec(self) -> int:
        """
        Runs the application.

        Returns:
            The exit code.
        """

        self._ensureLanguageIsSelected()

        if not self._projectManager.ensureModelsAreDownloaded():
            return 1

        from .Main.ProjectExplorerPage import ShellWindow  # Avoid circular imports
        self._shell = ShellWindow()
        self._shell.showMaximized()

        self._imageProcessorService.start()

        exitCode = super().exec()

        self._imageProcessorService.terminate()

        Application._instance = None
        return exitCode

    def icon(self) -> QtGui.QIcon:
        """
        Returns the application icon.
        """
        return self._icon

    def modelsDownloader(self) -> ModelsDownloader:
        """
        Returns the models downloader.
        """
        return self._modelsDownloader

    def shell(self):
        """
        Returns the shell window.
        """
        return self._shell

    def initLanguage(self):
        """
        Initializes the language.
        """
        langCode = SettingsService.instance().get("language", "en")
        LocalizationService.instance().set_locale(langCode)

    def _ensureLanguageIsSelected(self):
        """
        Ensures the language is selected.
        """
        langCode = SettingsService.instance().get("language", None)
        if langCode is None:
            from .LanguageWindow import LanguageWindow
            langWindow = LanguageWindow(parent=None, needsRestart=False)
            langWindow.exec()
