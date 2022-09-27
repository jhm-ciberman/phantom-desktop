from PySide6 import QtGui, QtCore, QtWidgets


class PixmapDisplay(QtWidgets.QWidget):

    imageRectChanged = QtCore.Signal(QtCore.QRect)

    """
    Widget for displaying a QPixmap. The image is scaled proportionally to fit the widget.
    This class can also be used as a base class for editors that display an image.
    """
    def __init__(self, pixmap: QtGui.QPixmap = None):
        """
        Initializes the PixmapDisplay class.

        Args:
            pixmap (QPixmap): The pixmap to display. Defaults to None.
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._pixmap = None
        self._resizedPixmap = None
        self._imageRect = None  # type: QtCore.QRect
        self._aspectRatioMode = QtCore.Qt.AspectRatioMode.KeepAspectRatio
        self._transformationMode = QtCore.Qt.TransformationMode.SmoothTransformation
        self._imageToWidgetTransform = QtGui.QTransform()
        self._widgetToImageTransform = QtGui.QTransform()
        self._isDirty = True
        self._isInPaintEvent = False  # Used to prevent recursive calls to repaint()
        pixmap is not None and self.setPixmap(pixmap)

    def repaint(self) -> None:
        """
        Repaints the widget.
        """
        if not self._isInPaintEvent:
            super().repaint()

    def setPixmap(self, pixmap: QtGui.QPixmap) -> None:
        """
        Sets the pixmap to display.

        Args:
            pixmap (QPixmap): The pixmap to display.
        """
        self._pixmap = pixmap
        self._isDirty = True
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
        self._isDirty = True
        self.repaint()

    def transformationMode(self) -> QtCore.Qt.TransformationMode:
        """
        Gets the transformation mode to use when scaling the image.
        """
        return self._transformationMode

    def setAspectRatioMode(self, aspectRatioMode: QtCore.Qt.AspectRatioMode) -> None:
        """
        Sets the aspect ratio mode to use when scaling the image.
        """
        self._aspectRatioMode = aspectRatioMode
        self._isDirty = True
        self.repaint()

    def aspectRatioMode(self) -> QtCore.Qt.AspectRatioMode:
        """
        Gets the aspect ratio mode to use when scaling the image.
        """
        return self._aspectRatioMode

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        self._isInPaintEvent = True
        self._processDirty()

        super().paintEvent(event)

        if self._resizedPixmap is not None:
            QtGui.QPainter(self).drawPixmap(self._imageRect, self._resizedPixmap)

        self._isInPaintEvent = False

    def imageRectChangedEvent(self, imageRect: QtCore.QRect) -> None:
        """
        Called when the image rectangle changes. This method can be overriden
        in derived classes to perform custom actions when the image rectangle changes.
        The rectangle can be null if there is no image.
        """
        self.imageRectChanged.emit(imageRect)

    def _processDirty(self) -> None:
        if not self._isDirty:
            return

        oldRect = self._imageRect
        self._isDirty = False
        if self._pixmap is not None:
            widgetW, widgetH = self.width(), self.height()
            imageW, imageH = self._pixmap.width(), self._pixmap.height()
            self._resizedPixmap = self._pixmap.scaled(widgetW, widgetH, self._aspectRatioMode, self._transformationMode)

            w, h = self._resizedPixmap.width(), self._resizedPixmap.height()
            x, y = (widgetW - w) / 2, (widgetH - h) / 2
            self._imageRect = QtCore.QRect(x, y, w, h)

            # Now we cache the 2d transformation matrix for convenience
            self._imageToWidgetTransform = QtGui.QTransform()
            self._imageToWidgetTransform.translate(x, y)
            self._imageToWidgetTransform.scale(w / imageW, h / imageH)

            self._widgetToImageTransform = QtGui.QTransform()
            self._widgetToImageTransform.scale(imageW / w, imageH / h)
            self._widgetToImageTransform.translate(-x, -y)
        else:
            self._resizedPixmap = None
            self._imageRect = None
            self._imageToWidgetTransform = QtGui.QTransform()
            self._widgetToImageTransform = QtGui.QTransform()

        if oldRect != self._imageRect:
            self.imageRectChangedEvent(self._imageRect)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._isDirty = True

    def widgetToImageTransform(self) -> QtGui.QTransform:
        """
        Gets the transform that converts points from the widget's coordinate system to the image's coordinate system.
        """
        self._processDirty()
        return self._widgetToImageTransform

    def imageToWidgetTransform(self) -> QtGui.QTransform:
        """
        Gets the transform that converts points from the image's coordinate system to the widget's coordinate system.
        """
        self._processDirty()
        return self._imageToWidgetTransform

    def imageRect(self) -> QtCore.QRect:
        """
        Gets the rectangle that the image is drawn into.
        """
        self._processDirty()
        return self._imageRect
