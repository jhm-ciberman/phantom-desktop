from PySide6 import QtGui, QtCore
from .PixmapDisplay import PixmapDisplay


class PixmapPointsDisplay(PixmapDisplay):
    """
    A widget that displays a preview of the selected image.
    """

    onPointsChanged = QtCore.Signal()

    onFinished = QtCore.Signal()

    def __init__(self):
        """
        Initializes the PixmapPreview class.
        """
        super().__init__()
        self.setMinimumHeight(200)
        self.setMinimumWidth(200)
        self.setMouseTracking(True)
        self._pointsImageSpace = []  # type: list[QtCore.QPoint]
        self._pointsWidgetSpace = []  # type: list[QtCore.QPoint]

        self._cursorPoint = None  # type: QtCore.QPoint
        self._hasFinished = False
        self._hightlightedPointIndex = -1  # type: int
        self._draggedPointIndex = -1  # type: int
        self._pointHitAreaRadius = 15  # type: int
        self._requiredPoints = 4  # type: int

        self._zoomRectSourceSize = 25  # type: int
        self._zoomRectDestSize = 200  # type: int
        self._zoomCrosshairSize = 6  # type: int
        self._zoomFactor = self._zoomRectDestSize / self._zoomRectSourceSize
        # Visual settings
        self._pointsPen = QtGui.QPen(QtGui.QColor("#583879"), 6)
        self._highlightedPointPen = QtGui.QPen(QtGui.QColor("#EFD547"), 10)
        self._editingLinePen = QtGui.QPen(QtGui.QColor("#CCC"), 2)
        self._finishedlinePen = QtGui.QPen(QtGui.QColor("#FFF"), 2)
        self._zoomCrosshairPen = QtGui.QPen(QtGui.QColor("#FFF"), self._zoomFactor)
        self._zoomBackgroundBrush = QtGui.QBrush(QtGui.QColor("#808080"))  # pure gray

        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)

    def addPoint(self, point: QtCore.QPoint):
        """
        Adds a point to the preview. The point must be in the image's coordinate system.
        """
        point = self._clampToImage(point)
        self._pointsImageSpace.append(point)
        self._pointsWidgetSpace.append(self.imageToWidgetTransform().map(point))
        self.onPointsChanged.emit()
        self.repaint()

    def setPoint(self, index: int, point: QtCore.QPoint):
        """
        Sets a point. The point must be in the image's coordinate system.
        """
        if index < 0 or index >= len(self._pointsImageSpace):
            return
        point = self._clampToImage(point)
        self._pointsImageSpace[index] = point
        self._pointsWidgetSpace[index] = self.imageToWidgetTransform().map(point)
        self.onPointsChanged.emit()
        self.repaint()

    def removePoint(self, index: int):
        """
        Removes a point.
        """
        if index < 0 or index >= len(self._pointsImageSpace):
            return
        self._pointsImageSpace.pop(index)
        self._pointsWidgetSpace.pop(index)
        self.onPointsChanged.emit()
        self.repaint()

    def clearPoints(self) -> None:
        """
        Clears the points.
        """
        self._pointsImageSpace.clear()
        self._pointsWidgetSpace.clear()
        self._hasFinished = False
        self.onPointsChanged.emit()
        self.repaint()

    def points(self) -> list[QtCore.QPoint]:
        """
        Gets the points. The points are in the image's coordinate system.
        """
        return self._pointsImageSpace

    def hasFinished(self) -> bool:
        """
        Gets whether the user has finished drawing the polygon.
        """
        return self._hasFinished

    def imageRectChangedEvent(self, imageRect: QtCore.QRect) -> None:
        """
        Called when the image rectangle changes. This method can be overriden
        in derived classes to perform custom actions when the image rectangle changes.
        The rectangle can be null if there is no image.
        """
        super().imageRectChangedEvent(imageRect)

        # Recompute the points in widget space
        transform = self.imageToWidgetTransform()
        self._pointsWidgetSpace = [transform.map(point) for point in self._pointsImageSpace]

    def paintEvent(self, event: QtGui.QPaintEvent):
        """
        Paints the widget.
        """
        super().paintEvent(event)
        painter = QtGui.QPainter(self)

        points = self._pointsWidgetSpace

        # Invert colors
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.RasterOp_SourceXorDestination)

        # (AA not suported in raster XOR mode)
        # painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        if self._hasFinished:
            painter.setPen(self._finishedlinePen)
            painter.drawPolygon(points)
        elif len(points) > 0:
            painter.setPen(self._editingLinePen)
            painter.drawPolyline(points)
            painter.drawLine(points[-1], self._cursorPoint)

        # Return to normal composition mode
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_SourceOver)

        for i, point in enumerate(points):
            if i == self._hightlightedPointIndex:
                painter.setPen(self._highlightedPointPen)
            else:
                painter.setPen(self._pointsPen)
            painter.drawPoint(point)

        if not self._hasFinished or self._draggedPointIndex != -1:
            self._drawZoomRect(painter)

    def _drawZoomRect(self, painter: QtGui.QPainter):
        """
        Draws the zoom rect.
        """
        # Draw zoom rect
        if self._cursorPoint is None:
            return
        cursorDest, cursorSource = self._cursorPoint, self._widgetToImage(self._cursorPoint)
        pixmap = self.pixmap()

        srcW, srcH = self._zoomRectSourceSize, self._zoomRectSourceSize
        srcX, srcY = cursorSource.x() - srcW // 2, cursorSource.y() - srcH // 2

        destX, destY = 0, 0
        destW, destH = self._zoomRectDestSize, self._zoomRectDestSize
        if cursorDest.x() < destW + 20 and cursorDest.y() < destH + 20:
            destX = self.width() - destW

        painter.setBrush(self._zoomBackgroundBrush)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(destX, destY, destW, destH)

        painter.drawPixmap(destX, destY, destW, destH, pixmap, srcX, srcY, srcW, srcH)

        # Draw a crosshair (4 lines, leaving the center pixel visible) with inverted colors
        cx, cy = destX + destW // 2, destY + destH // 2
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.RasterOp_SourceXorDestination)
        painter.setPen(self._zoomCrosshairPen)
        p = self._zoomFactor  # 1 pixel in source space is p pixels in dest space
        s = self._zoomCrosshairSize * p  # size of the crosshair in source space
        pp = 2 * p  # 2 pixels in source space for the inner space of the crosshair

        painter.drawLine(cx - s, cy, cx - pp, cy)  # left
        painter.drawLine(cx + pp, cy, cx + s, cy)  # right
        painter.drawLine(cx, cy - s, cx, cy - pp)  # top
        painter.drawLine(cx, cy + pp, cx, cy + s)  # bottom

    def _widgetToImage(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """
        Converts a point from widget space to image space and clamps it to the image's bounds.
        """
        point = self.widgetToImageTransform().map(point)
        point = self._clampToImage(point)
        return point

    def _clampToImage(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """
        Clamps a point to the image's bounds.
        """
        pixmapSize = self.pixmap().size()
        x = max(0, min(point.x(), pixmapSize.width()))
        y = max(0, min(point.y(), pixmapSize.height()))
        return QtCore.QPoint(x, y)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        Handles mouse press events.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self._hasFinished and self._hightlightedPointIndex >= 0:
                # Start dragging a point
                self._draggedPointIndex = self._hightlightedPointIndex
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            if not self._hasFinished:
                # Remove the last point
                if len(self._pointsImageSpace) > 0:
                    self._pointsImageSpace.pop()
                    self._pointsWidgetSpace.pop()
                    self.onPointsChanged.emit()
                    self.repaint()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """
        Handles mouse move events.
        """
        self._cursorPoint = event.pos()
        cursorPosInImageSpace = self._widgetToImage(event.pos())

        if self._draggedPointIndex >= 0:
            # Drag a point
            self.setPoint(self._draggedPointIndex, cursorPosInImageSpace)
        elif self._hasFinished:
            # Check if the cursor is over a point
            self._hightlightedPointIndex = -1
            minDist = self._pointHitAreaRadius
            for i, point in enumerate(self._pointsWidgetSpace):
                distance = (point - event.pos()).manhattanLength()
                if distance < minDist:
                    self._hightlightedPointIndex = i
                    minDist = distance

        self._updateCursor()
        self.repaint()

    def _updateCursor(self):
        if self._draggedPointIndex >= 0:
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        elif self._hightlightedPointIndex >= 0:
            self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        elif not self._hasFinished:
            self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """
        Handles mouse release events.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self._draggedPointIndex >= 0:
                # Stop dragging a point
                self._draggedPointIndex = -1
            elif not self._hasFinished:
                # Add a point
                point = self._widgetToImage(event.pos())
                self.addPoint(point)
                if len(self._pointsImageSpace) == self._requiredPoints:
                    self._hasFinished = True
                    self.onFinished.emit()
            self._updateCursor()
            self.repaint()
