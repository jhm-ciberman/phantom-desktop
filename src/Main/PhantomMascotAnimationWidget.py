from PySide6 import QtCore, QtGui, QtWidgets
import math
import random
from time import time_ns


class AnimationBase(QtWidgets.QWidget):
    """
    A base abstract class for frame based animations. Provides a simple render loop with update/draw method.
    """
    _animationFPS = 60  # frames per second

    _lastUpdateTime = 0

    _canvasWidth: int = 0

    _canvasHeight: int = 0

    _time: float = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._lastUpdateTime = time_ns() * 1e-9  # seconds

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._onUpdateTimer)
        self._timer.start(1000 / self._animationFPS)

    def _onUpdateTimer(self):
        self._time = time_ns() * 1e-9  # seconds
        dt = self._time - self._lastUpdateTime
        self._lastUpdateTime = self._time

        self._update(dt, self._time)

        super().update()  # Queue QT paint event

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        self._draw(painter)

    def _update(self, dt: float, time: float):
        """
        Override this method to update the animation.
        """
        pass

    def _draw(self, painter: QtGui.QPainter):
        """
        Override this method to draw the animation.
        """
        pass

    def sizeHint(self):
        return QtCore.QSize(self._canvasWidth, self._canvasHeight)


class PhantomMascotAnimationWidget(AnimationBase):
    """
    A small animated image with two frames. One with the eyes open and one with the eyes closed.
    The image is a ghost that moves from left to right and back with a small easing effect.
    Also it has a small floating effect (up and down, sinusoidal).
    """

    _mascot: "PhantomMascotPatrol"

    _tumbleweed: "Tumbleweed"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._canvasWidth = 400
        self._canvasHeight = 200
        self._mascot = PhantomMascotPatrol(moveStartX=100, moveEndX=300, baseY=90)
        self._tumbleweedBack = Tumbleweed(moveStartX=50, moveEndX=350, baseY=110, scale=0.5, alphaMulti=0.6, hspeed=40)
        self._tumbleweedFront = Tumbleweed(moveStartX=40, moveEndX=360, baseY=160, scale=0.8, alphaMulti=1.0, hspeed=60)

    def _update(self, dt: float, time: float):
        self._mascot.update(dt, time)
        self._tumbleweedBack.update(dt, time)
        self._tumbleweedFront.update(dt, time)

    def _draw(self, painter: QtGui.QPainter):
        self._tumbleweedBack.draw(painter)
        self._mascot.draw(painter)
        self._tumbleweedFront.draw(painter)


class PhantomMascot:
    frameIdle = QtGui.QImage("res/img/phantom_mascot_idle.png")  # 128x128
    """The idle frame of the mascot."""

    frameBlink = QtGui.QImage("res/img/phantom_mascot_blink.png")
    """The blinking frame of the mascot."""

    blinkDurationMin = 40
    """The minimum duration in milliseconds when the mascot will have its eyes closed."""

    blinkDurationMax = 250
    """The maximum duration in milliseconds when the mascot will have its eyes closed."""

    blinkIntervalMin = 800
    """The minimum interval between two blinks in milliseconds."""

    blinkIntervalMax = 4000
    """The maximum interval between two blinks in milliseconds."""

    currentFrame = frameIdle
    """The current frame of the mascot."""

    facing = 1  # 1 = right, -1 = left
    """A value of 1 means the mascot is facing right, a value of -1 means the mascot is facing left."""

    x = 0
    """The x position of the mascot without having the "floating" effect applied."""

    y = 0
    """The y position of the mascot without having the "floating" effect applied."""

    floatingDeltaY = 15
    """The delta y value for the "floating" effect."""

    floatingDeltaX = 10
    """The delta x value for the "floating" effect."""

    floatingSpeed = 0.5  # Cycles per second
    """The speed of the "floating" effect measured in cycles per second."""

    _floatingX = 0

    _floatingY = 0

    _transform: QtGui.QTransform()

    def __init__(self) -> None:
        self._blinkTimer = QtCore.QTimer()
        self._blinkTimer.setSingleShot(True)
        self._blinkTimer.timeout.connect(self._onBlinkTimerTimeout)

        self._transform = QtGui.QTransform()
        self._onBlinkTimerTimeout()
        self.updateTransform()

    def _onBlinkTimerTimeout(self):
        isBlinking = self.currentFrame == self.frameBlink

        if isBlinking:
            self.currentFrame = self.frameIdle
            self._blinkTimer.start(random.randint(self.blinkIntervalMin, self.blinkIntervalMax))
        else:
            self.currentFrame = self.frameBlink
            self._blinkTimer.start(random.randint(self.blinkDurationMin, self.blinkDurationMax))

    def update(self, dt: float, t: float):
        self._floatingX = math.sin(t * self.floatingSpeed * 0.3 * math.pi * 2) * self.floatingDeltaX
        self._floatingY = math.sin(t * self.floatingSpeed * math.pi * 2) * self.floatingDeltaY
        self.updateTransform()

    def updateTransform(self):
        self._transform.reset()
        self._transform.translate(self.x + self._floatingX, self.y + self._floatingY)
        self._transform.scale(-self.facing, 1)

    def draw(self, painter: QtGui.QPainter):
        w, h = self.currentFrame.width(), self.currentFrame.height()
        painter.setTransform(self._transform)
        painter.drawImage(-w / 2, -h / 2, self.currentFrame)
        painter.resetTransform()


class PhantomMascotPatrol(PhantomMascot):
    movingStartX = 0

    movingEndX = 0  # from 0 to +moveDeltaX inside the widget

    movingSpeed = 40  # pixels per second

    _rawX = 0  # This is X before easing

    _easingX = None

    def __init__(self, moveStartX: int, moveEndX: int, baseY: int) -> None:
        super().__init__()
        self._easingX = QtCore.QEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.movingStartX = moveStartX
        self.movingEndX = moveEndX
        self.y = baseY

    @property
    def movingDeltaX(self):
        return self.movingEndX - self.movingStartX

    def update(self, dt: float, t: float):
        self._rawX += self.movingSpeed * self.facing * dt

        moveDeltaX = self.movingEndX - self.movingStartX
        progress = (self._rawX - self.movingStartX) / moveDeltaX
        self.x = self._easingX.valueForProgress(progress) * moveDeltaX + self.movingStartX

        minX = self.movingStartX
        maxX = self.movingEndX
        if self._rawX < minX:
            self._rawX = minX
            self.facing = 1
        elif self._rawX > maxX:
            self._rawX = maxX
            self.facing = -1

        super().update(dt, t)


class Tumbleweed:

    _frame = QtGui.QImage("res/img/tumbleweed.png")

    _intervalMin = 3000

    _intervalMax = 8000

    _angle = 0  # degrees

    _rotationSpeed = 0.5  # cycles per second

    _bounceDeltaY = 15  # From (0,0) to (0, bounceDeltaY) and back

    _bounceSpeedMin = 0.5  # cycles per second

    _bounceSpeedMax = 1.5  # cycles per second

    _bounceSpeed = 0  # cycles per second

    _movingSpeedX = 60  # pixels per second

    _movingStartX = 0

    _movingEndX = 0  # from 0 to +moveDeltaX inside the widget

    _fadeMargin = 64

    _x = 0  # 0,0 is the desired start position of the thumbleweed

    _y = 0

    _alpha = 0

    _alphaMulti: float = 1.0

    _baseY = 0  # The base "floor" position

    _easeY: QtCore.QEasingCurve

    _scale = 1

    _transform: QtGui.QTransform

    _isMoving = False

    def __init__(
            self, moveStartX: int, moveEndX: int, baseY: int,
            scale: float = 1.0, alphaMulti: float = 1.0, hspeed: float = 60) -> None:
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._onTimerTimeout)
        self._timer.start(random.randint(self._intervalMin, self._intervalMax))

        self._easeY = QtCore.QEasingCurve(QtCore.QEasingCurve.OutQuad)

        self._movingStartX = moveStartX
        self._movingEndX = moveEndX
        self._baseY = baseY
        self._scale = scale
        self._alphaMulti = alphaMulti
        self._movingSpeedX = hspeed

        self._transform = QtGui.QTransform()
        self._alpha = 0

        self._startTimer()

    def _startTimer(self):
        if self._timer.isActive():
            return
        self._timer.start(random.randint(self._intervalMin, self._intervalMax))

    def _onTimerTimeout(self):
        self._x = self._movingStartX
        self._y = self._baseY
        self._isMoving = True
        self._bounceSpeed = random.uniform(self._bounceSpeedMin, self._bounceSpeedMax)

    def update(self, dt: float, t: float):
        if self._isMoving:
            if self._x < self._movingEndX:
                self._x += self._movingSpeedX * dt
                self._angle += dt * self._rotationSpeed * 360

                t = self._pingPong(t * self._bounceSpeed)
                self._y = self._baseY - self._easeY.valueForProgress(t) * self._bounceDeltaY
            else:
                self._isMoving = False
                self._startTimer()

        self._alpha = 1
        if self._x < self._movingStartX + self._fadeMargin:
            self._alpha = (self._x - self._movingStartX) / self._fadeMargin
        elif self._x > self._movingEndX - self._fadeMargin:
            self._alpha = (self._movingEndX - self._x) / self._fadeMargin

        self._transform.reset()
        self._transform.translate(self._x, self._y)
        self._transform.rotate(self._angle)
        self._transform.scale(self._scale, self._scale)

    def draw(self, painter: QtGui.QPainter):
        w, h = self._frame.width(), self._frame.height()
        painter.setTransform(self._transform)
        painter.setOpacity(self._alpha * self._alphaMulti)
        painter.drawImage(-w / 2, -h / 2, self._frame)
        painter.setOpacity(1)
        painter.resetTransform()

    def _pingPong(self, t: float):
        t = t % 1
        if t < 0.5:
            return t * 2
        else:
            return 1 - (t - 0.5) * 2


class PhantomMascotLangAnimation(AnimationBase):
    """
    A small animation that shows the phantom mascot floating with a lang icon above his head.
    """

    _langIcon = QtGui.QImage("res/img/lang.png")

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self._canvasWidth = 200
        self._canvasHeight = 200

        self._mascot = PhantomMascot()
        self._mascot.y = 114
        self._mascot.x = 94
        self._mascot.floatingDeltaX = 5
        self._mascot.floatingDeltaY = 10
        self._mascot.floatingSpeed = 0.3
        self._mascot.facing = -1

    def _update(self, dt: float, t: float):
        self._mascot.update(dt, t)

    def _draw(self, painter: QtGui.QPainter):
        # lang icon at top right
        rect = QtCore.QRect(self._canvasWidth - 64, 0, 64, 64)
        painter.drawImage(rect, self._langIcon)

        # phantom mascot in the center of remaining space
        self._mascot.draw(painter)
