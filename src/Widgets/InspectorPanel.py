from PySide6 import QtGui, QtCore, QtWidgets
from Image import Image
from Widgets.PixmapDisplay import PixmapDisplay

class InspectorPanel(QtWidgets.QWidget):
    """
    A widget that displays a the properties of an image or a group of images.
    """
    def __init__(self):
        """
        Initializes the InspectorPanel class.
        """
        super().__init__()

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self.setContentsMargins(0, 0, 0, 0)

        self._frame = QtWidgets.QFrame()
        self._frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self._frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self._frame.setContentsMargins(0, 0, 0, 0)
        self._frameLayout = QtWidgets.QVBoxLayout()
        self._frameLayout.setContentsMargins(0, 0, 0, 0)
        self._frame.setLayout(self._frameLayout)

        self._layout.addWidget(self._frame)

        self._pixmapDisplay = PixmapDisplay()
        self.setMinimumWidth(200)
        self._layout.addWidget(self._pixmapDisplay)
        
        self._selectedImages = []

    def setSelectedImages(self, images: list[Image]):
        """
        Sets the selected images.
        """
        self._selectedImages = images

        if len(self._selectedImages) == 1:
            image = self._selectedImages[0]
            qimage = QtGui.QImage(image.raw_image, image.width, image.height, QtGui.QImage.Format_RGBA8888)
            self._pixmapDisplay.setPixmap(QtGui.QPixmap.fromImage(qimage))
        else:
            self._pixmapDisplay.setPixmap(None)

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages