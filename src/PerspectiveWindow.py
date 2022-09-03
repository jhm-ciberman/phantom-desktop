from tkinter import Image
from PySide6 import QtGui, QtCore, QtWidgets
from .Image import Image
from .Widgets.PixmapPointsDisplay import PixmapPointsDisplay


class PerspectiveWindow(QtWidgets.QWidget):
    def __init__(self, image: Image) -> None:
        super().__init__()
        icon = QtGui.QIcon("res/icon_128.png")
        self.setWindowIcon(icon)
        self.setWindowTitle(str(image.basename) + " - Phantom")
        self.setMinimumSize(800, 600)

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._image = image
        
        self._gridLayout = QtWidgets.QGridLayout() # Used to overlay the points preview
        self._layout.addLayout(self._gridLayout)

        self._pixmapPointsDisplay = PixmapPointsDisplay()
        self._pixmapPointsDisplay.setMinimumHeight(200)
        self._pixmapPointsDisplay.setMinimumWidth(200)
        self._pixmapPointsDisplay.setPixmap(self._image.pixmap)
        self._gridLayout.addWidget(self._pixmapPointsDisplay, 0, 0)

        self._frame = QtWidgets.QFrame()
        self._frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self._frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self._frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self._frame.setMinimumWidth(200)
        self._frameLayout = QtWidgets.QFormLayout()
        self._frameLayout.setContentsMargins(10, 10, 10, 10)
        self._frame.setLayout(self._frameLayout)

        self._layout.addWidget(self._frame)

        self._points = []

