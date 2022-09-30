from PySide6 import QtGui, QtCore, QtWidgets
from .ImageFeaturesService import ImageFeaturesService
from .Main.MainWindow import MainWindow
import sys


class Application(QtWidgets.QApplication):
    def __init__(self, args):
        super().__init__(args)
        self._icon = QtGui.QIcon("res/icon_128.png")
        self.setWindowIcon(self._icon)

        # self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

        p = self.palette()
        p.setColor(QtGui.QPalette.Window, QtCore.Qt.white)
        self.setPalette(p)

        self.setStyleSheet("""
            QStatusBar { background-color: #f0f0f0; }
        """)

    def run(self):
        win = MainWindow()
        win.showMaximized()

        exitCode = self.exec()

        ImageFeaturesService.instance().terminate()

        sys.exit(exitCode)
