from PySide6 import QtCore, QtWidgets, QtGui


class LoadingIcon(QtWidgets.QWidget):
    """
    A simple loading icon that can be used to indicate that the application is busy.
    """
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initializes a new instance of the LoadingIcon class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        self._speed: float = 1.0  # rotations per second
        self._angle: float = 0  # degrees

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._onTimeout)
        self._timer.start(self._getTimerInterval())

        self._image = QtGui.QImage("res/img/spinner.png")

        self.setFixedSize(32, 32)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def speed(self) -> float:
        """Gets the speed of the animation measured in rotations per second."""
        return self._speed

    def setSpeed(self, value: float) -> None:
        """Sets the speed of the animation measured in rotations per second."""
        self._speed = value
        self._timer.setInterval(self._getTimerInterval())

    def _getTimerInterval(self) -> int:
        return int(1000 / self._speed / 8)

    def _onTimeout(self) -> None:
        self._angle = (self._angle + 45) % 360
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)

        # draw scaled image
        painter.drawImage(
            QtCore.QRect(-self.width() / 2, -self.height() / 2, self.width(), self.height()),
            self._image)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(32, 32)
