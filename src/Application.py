import sys

from PySide6 import QtCore, QtGui, QtWidgets

from .Workspace import Workspace


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
        Returns the ProjectManager instance.
        """
        # ProjectManager is not a singleton because this will enable
        # in a future to have multiple projects open at the same time.
        return Application.instance()._projectManager

    def __init__(self, args):
        """
        Initializes a new instance of the Application class.
        """
        super().__init__(args)
        if Application._instance is not None:
            raise Exception("Application instance already created")

        Application._instance = self

        self._icon = QtGui.QIcon("res/img/icon_128.png")
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
        self._projectManager = Workspace(self._imageProcessorService)

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
