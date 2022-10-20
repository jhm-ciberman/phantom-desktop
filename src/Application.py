import sys

from PySide6 import QtCore, QtGui, QtWidgets

from .ProjectManager import ProjectManager
from .Workspace import Workspace

app_version = "1.0.0"
app_name = "Phantom Desktop"
repo_url = "https://github.com/jhm-ciberman/phantom-desktop"
docs_url = "https://github.com/jhm-ciberman/phantom-desktop/wiki"
bug_report_url = "https://github.com/jhm-ciberman/phantom-desktop/issues/new"


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

        self.setApplicationVersion(app_version)
        self.setApplicationName(app_name)

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

    def run(self):
        """
        Runs the application.
        """
        from .Main.MainWindow import MainWindow  # Avoid circular importss
        win = MainWindow()
        win.showMaximized()

        self._imageProcessorService.start()

        exitCode = self.exec()

        self._imageProcessorService.terminate()

        sys.exit(exitCode)

    def icon(self) -> QtGui.QIcon:
        """
        Returns the application icon.
        """
        return self._icon

    def docsUrl(self) -> str:
        """
        Returns the help URL.
        """
        return docs_url

    def repoUrl(self) -> str:
        """
        Returns the repository URL.
        """
        return repo_url

    def bugReportUrl(self) -> str:
        """
        Returns the bug report URL.
        """
        return bug_report_url
