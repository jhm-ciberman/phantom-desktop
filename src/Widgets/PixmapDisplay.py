from PySide6 import QtGui, QtCore, QtWidgets

class PixmapDisplay(QtWidgets.QWidget):
    """
    Widget for displaying a QPixmap. The image is scaled proportionally to fit the widget.
    """
    def __init__(self, pixmap: QtGui.QPixmap = None):
        """
        Initializes the PixmapDisplay class.

        Args:
            pixmap (QPixmap): The pixmap to display.
        """
        super().__init__()
        self._pixmap = None
        self._transformationMode = QtCore.Qt.TransformationMode.SmoothTransformation
        pixmap is not None and self.setPixmap(pixmap)

    def setPixmap(self, pixmap: QtGui.QPixmap) -> None:
        """
        Sets the pixmap to display.

        Args:
            pixmap (QPixmap): The pixmap to display.
        """
        self._pixmap = pixmap
        self.repaint()

    def pixmap(self) -> QtGui.QPixmap:
        """
        Gets the pixmap to display.
        """
        return self._pixmap

    def setTransformationMode(self, transformationMode: QtCore.Qt.TransformationMode) -> None:
        """
        Sets the transformation mode to use when scaling the image.
        """
        self._transformationMode = transformationMode

    def transformationMode(self) -> QtCore.Qt.TransformationMode:
        """
        Gets the transformation mode to use when scaling the image.
        """
        return self._transformationMode

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        if self._pixmap is not None:
            imageWidth, imageHeight = self._pixmap.width(), self._pixmap.height()
            labelWidth, labelHeight = self.width(), self.height()
            ratio = min(labelWidth / imageWidth, labelHeight / imageHeight)
            newWidth, newHeight = int(imageWidth * ratio), int(imageHeight * ratio)
            newPixmap = self._pixmap.scaledToWidth(newWidth, self._transformationMode)
            x, y = abs(newWidth - labelWidth) // 2, abs(newHeight - labelHeight) // 2
            QtGui.QPainter(self).drawPixmap(x, y, newPixmap)

