from PySide6 import QtGui, QtCore, QtWidgets
from .Models import Project


class Application(QtWidgets.QApplication):
    """
    This class is a singleton that represents the application.
    """

    _instance = None

    @staticmethod
    def instance() -> "Application":
        if Application._instance is None:
            raise Exception("Application instance not created yet")
        return Application._instance

    def __init__(self, args):
        super().__init__(args)
        if Application._instance is not None:
            raise Exception("Application instance already created")

        Application._instance = self

        self._icon = QtGui.QIcon("res/icon_128.png")
        self.setWindowIcon(self._icon)

        # self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

        p = self.palette()
        p.setColor(QtGui.QPalette.Window, QtCore.Qt.white)
        self.setPalette(p)

        self.setStyleSheet("""
            QStatusBar { background-color: #f0f0f0; }
        """)

        self._project: Project = Project()

    def run(self):
        from .ImageFeaturesService import ImageFeaturesService
        from .Main.MainWindow import MainWindow
        import sys
        win = MainWindow()
        win.showMaximized()

        exitCode = self.exec()

        ImageFeaturesService.instance().terminate()

        sys.exit(exitCode)

    def icon(self):
        return self._icon

    def setCurrentProject(self, project: Project):
        """
        Sets the current project.

        Args:
            project (Project): The project to set as current.
        """
        self._project = project

    def currentProject(self) -> Project:
        """
        Returns the current project.

        Returns:
            Project: The current project.
        """
        return self._project
