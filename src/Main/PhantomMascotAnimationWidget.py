from PySide6 import QtCore, QtGui, QtWidgets
import math
import random
from time import time_ns


class PhantomMascotAnimationWidget(QtWidgets.QWidget):
    """
    A small animated image with two frames. One with the eyes open and one with the eyes closed.
    The image is a ghost that moves from left to right and back with a small easing effect.
    Also it has a small floating effect (up and down, sinusoidal).
    """

    _animationFPS = 60  # frames per second

    _lastUpdateTime = 0

    _mascot: "PhantomMascot"

    _tumbleweed: "Tumbleweed"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(1000 / self._animationFPS)

        self._lastUpdateTime = time_ns() * 1e-9  # seconds

        self._width = 400
        self._height = 200
        self._mascot = PhantomMascot(moveStartX=100, moveEndX=300, baseY=90)
        self._tumbleweedBack = Tumbleweed(moveStartX=50, moveEndX=350, baseY=110, scale=0.5, alphaMulti=0.6, hspeed=40)
        self._tumbleweedFront = Tumbleweed(moveStartX=40, moveEndX=360, baseY=160, scale=0.8, alphaMulti=1.0, hspeed=60)

    def _update(self):
        t = time_ns() * 1e-9  # seconds
        dt = t - self._lastUpdateTime
        self._lastUpdateTime = t

        self._mascot.update(dt, t)
        self._tumbleweedBack.update(dt, t)
        self._tumbleweedFront.update(dt, t)

        self.update()  # Queue QT paint event

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        self._tumbleweedBack.draw(painter)
        self._mascot.draw(painter)
        self._tumbleweedFront.draw(painter)

    def sizeHint(self):
        return QtCore.QSize(self._width, self._height)


class PhantomMascot:
    frameIdle = QtGui.QImage("res/img/phantom_mascot_idle.png")  # 128x128

    frameBlink = QtGui.QImage("res/img/phantom_mascot_blink.png")

    blinkDurationMin = 40

    blinkDurationMax = 250

    blinkIntervalMin = 800

    blinkIntervalMax = 4000

    floatingDeltaY = 15

    floatingDeltaX = 10

    floatingSpeedY = 0.5  # Cycles per second
    floatingSpeedX = 1.3  # Cycles per second

    movingStartX = 0

    movingEndX = 0  # from 0 to +moveDeltaX inside the widget

    movingSpeed = 40  # pixels per second

    currentFrame = frameIdle

    movingDirection = 1  # 1 = right, -1 = left

    x = 0  # 0,0 is the center of the widget

    y = 0

    _baseY = 80

    _baseX = 0

    rawX = 0  # This is X before easing

    easingX = None

    _transform: QtGui.QTransform()

    def __init__(self, moveStartX: int, moveEndX: int, baseY: int) -> None:
        self._blinkTimer = QtCore.QTimer()
        self._blinkTimer.setSingleShot(True)
        self._blinkTimer.timeout.connect(self._onBlinkTimerTimeout)

        self.easingX = QtCore.QEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.movingStartX = moveStartX
        self.movingEndX = moveEndX
        self._baseY = baseY

        self._transform = QtGui.QTransform()

        self._onBlinkTimerTimeout()

    def _onBlinkTimerTimeout(self):
        isBlinking = self.currentFrame == self.frameBlink

        if isBlinking:
            self.currentFrame = self.frameIdle
            self._blinkTimer.start(random.randint(self.blinkIntervalMin, self.blinkIntervalMax))
        else:
            self.currentFrame = self.frameBlink
            self._blinkTimer.start(random.randint(self.blinkDurationMin, self.blinkDurationMax))

    @property
    def movingDeltaX(self):
        return self.movingEndX - self.movingStartX

    def update(self, dt: float, t: float):
        self.rawX += self.movingSpeed * self.movingDirection * dt
        self.y = math.sin(t * self.floatingSpeedY * math.pi * 2) * self.floatingDeltaY + self._baseY
        floatingDeltaX = math.sin(t * self.floatingSpeedY * math.pi * 2) * self.floatingDeltaX

        moveDeltaX = self.movingEndX - self.movingStartX
        progress = (self.rawX - self.movingStartX) / moveDeltaX
        self.x = self.easingX.valueForProgress(progress) * moveDeltaX + self.movingStartX + floatingDeltaX

        minX = self.movingStartX
        maxX = self.movingEndX
        if self.rawX < minX:
            self.rawX = minX
            self.movingDirection = 1
        elif self.rawX > maxX:
            self.rawX = maxX
            self.movingDirection = -1

        self._transform.reset()
        self._transform.translate(self.x, self.y)
        self._transform.scale(-self.movingDirection, 1)

    def draw(self, painter: QtGui.QPainter):
        w, h = self.currentFrame.width(), self.currentFrame.height()
        painter.setTransform(self._transform)
        painter.drawImage(-w / 2, -h / 2, self.currentFrame)
        painter.resetTransform()


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
