import time
from typing import Callable
from PySide6 import QtCore, QtGui, QtWidgets
import math
import random
from time import time_ns


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


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


class Sprite:
    """
    A simple sprite.
    """

    frame: QtGui.QImage

    x = 0

    y = 0

    scaleX = 1

    scaleY = 1

    def __init__(self, image: str, x: int, y: int, scale: float = 1) -> None:
        self.frame = QtGui.QImage(image)
        self.x = x
        self.y = y
        self.scaleX = scale
        self.scaleY = scale

    def draw(self, painter: QtGui.QPainter):
        # pivot is center
        w, h = self.frame.width(), self.frame.height()

        painter.translate(self.x, self.y)
        painter.scale(self.scaleX, self.scaleY)
        painter.drawImage(-w / 2, -h / 2, self.frame)
        painter.resetTransform()


class SimpleTween:
    """A simple fire and forget tween"""

    def __init__(
            self, duration: float, easing: QtCore.QEasingCurve.Type,
            updateCallback: Callable[[float], None] = None,
            completeCallback: Callable[[], None] = None) -> None:
        """
        Initializes a new instance of the SimpleTween class.

        Args:
            duration: The duration of the tween in seconds.
            easing: The easing curve to use.
            updateCallback: The callback to call when the tween is updated. The callback will be called with a value
                indicating the progress of the tween between 0 and 1.
            completeCallback: The callback to call when the tween is complete.
        """
        self._duration = duration
        self._easing = QtCore.QEasingCurve(easing)
        self._updateCallback = updateCallback or (lambda _: None)
        self._completeCallback = completeCallback or (lambda: None)
        self._startTime = time.time()
        self._finished = False

    def update(self) -> bool:
        """Updates the tween and returns True if the tween has finished"""
        if self._finished:
            return True

        t = time.time() - self._startTime
        if t < self._duration:
            self._updateCallback(self._easing.valueForProgress(t / self._duration))
            return False
        else:
            self._updateCallback(1)
            self._completeCallback()
            self._finished = True
            return True

    @staticmethod
    def delay(duration: float, callback: Callable[[], None] = None) -> "SimpleTween":
        """
        Creates a new delay tween.

        Args:
            duration: The duration of the delay in seconds.
            callback: The callback to call when the delay is complete.
        """
        return SimpleTween(duration, QtCore.QEasingCurve.Linear, completeCallback=callback)


class GrabingPhantomMascot(PhantomMascot):
    """
    A phantom mascot that can hold one object in its hand.
    """

    _grabbedObject: Sprite = None

    _grabTween: SimpleTween = None

    _onCompleteCallback: Callable = None

    def __init__(self) -> None:
        super().__init__()

    def _getHandPosition(self) -> tuple[float, float]:
        point = QtCore.QPointF(-50, 4)
        point = self._transform.map(point)
        return point.x(), point.y()

    def grab(self, sprite: Sprite, onComplete: Callable[[], None] = None):
        """
        Grabs the given sprite.

        Args:
            sprite: The sprite to grab.
            onComplete: The callback to call when the grab is complete.
        """
        self._grabbedObject = sprite
        self._onCompleteCallback = onComplete or (lambda: None)
        xStart, yStart = sprite.x, sprite.y

        def _onComplete():
            self._grabTween = None
            self._onCompleteCallback()

        def _onProgress(t):
            nonlocal xStart, yStart
            handX, handY = self._getHandPosition()
            sprite.x = lerp(xStart, handX, t)
            sprite.y = lerp(yStart, handY, t)

        self._grabTween = SimpleTween(0.5, QtCore.QEasingCurve.OutCubic, _onProgress, _onComplete)

    def drop(self, x: int, y: int, onComplete: Callable[[], None] = None):
        """
        Drops the currently grabbed sprite.

        Args:
            x: The x position to drop the sprite at.
            y: The y position to drop the sprite at.
            onComplete: The callback to call when the drop is complete.
        """
        self._onCompleteCallback = onComplete or (lambda: None)
        xStart, yStart = self._getHandPosition()

        def _onComplete():
            self._grabbedObject = None
            self._grabTween = None
            self._onCompleteCallback()

        def _onProgress(t):
            nonlocal xStart, yStart
            self._grabbedObject.x = lerp(xStart, x, t)
            self._grabbedObject.y = lerp(yStart, y, t)

        self._grabTween = SimpleTween(0.5, QtCore.QEasingCurve.OutCubic, _onProgress, _onComplete)

    def update(self, dt: float, t: float):
        super().update(dt, t)
        if self._grabTween:
            self._grabTween.update()
        elif self._grabbedObject:
            self._grabbedObject.x, self._grabbedObject.y = self._getHandPosition()

    def draw(self, painter: QtGui.QPainter):
        super().draw(painter)
        if self._grabbedObject:
            self._grabbedObject.draw(painter)


class PhantomMascotFacesAnimation(AnimationBase):
    """
    This animation shows our phantom mascot taking photos from a box and placing them in 3 different boxes
    according to the photo type.
    """

    _mascot: GrabingPhantomMascot

    _sourceBox: Sprite

    _destBoxes: list[Sprite]

    _photos = [
        Sprite("res/img/photo1.png", 0, 0, 0.5),
        Sprite("res/img/photo2.png", 0, 0, 0.5),
        Sprite("res/img/photo3.png", 0, 0, 0.5),
    ]

    _currentPhoto: Sprite = None

    _tween: SimpleTween = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self._canvasWidth = 550
        self._canvasHeight = 200

        self._mascot = GrabingPhantomMascot()

        boxesY = 150
        self._sourceBox = Sprite("res/img/box.png", 50, boxesY)

        self._destBoxes = [
            Sprite("res/img/box.png", 300, boxesY),
            Sprite("res/img/box.png", 400, boxesY),
            Sprite("res/img/box.png", 500, boxesY),
        ]

        self._boxOffsetX = 60
        self._mascot.x = self._sourceBox.x + self._boxOffsetX
        self._mascot.y = self._sourceBox.y - 50

        self._nextPhoto()

    def _update(self, dt: float, time: float):
        self._mascot.update(dt, time)

        if self._tween:
            self._tween.update()

    def _draw(self, painter: QtGui.QPainter):
        # draw mascot behind boxes (Current photo is draw by the mascot)
        self._mascot.draw(painter)

        # draw boxes at the front
        self._sourceBox.draw(painter)
        for box in self._destBoxes:
            box.draw(painter)

    def _nextPhoto(self):
        prevPhoto = self._currentPhoto
        while prevPhoto == self._currentPhoto:
            index = random.randint(0, len(self._photos) - 1)
            self._currentPhoto = self._photos[index]
            self._destBox = self._destBoxes[index]

        self._currentPhoto.x = self._sourceBox.x
        self._currentPhoto.y = self._sourceBox.y + 20

        self._mascot.facing = -1
        self._mascot.grab(self._currentPhoto, onComplete=self._goToBox)

    def _goToBox(self):
        def _update(t):
            self._mascot.x = lerp(self._sourceBox.x + self._boxOffsetX, self._destBox.x - self._boxOffsetX, t)
        self._mascot.facing = 1
        duration = abs(self._mascot.x - self._destBox.x) / 100
        self._tween = SimpleTween(duration, QtCore.QEasingCurve.InOutQuad, _update, self._dropPhoto)

    def _dropPhoto(self):
        self._mascot.drop(self._destBox.x, self._destBox.y + 20, onComplete=self._returnToSource)

    def _returnToSource(self):
        def _update(t):
            self._mascot.x = lerp(self._destBox.x - self._boxOffsetX, self._sourceBox.x + self._boxOffsetX, t)
        self._mascot.facing = -1
        duration = abs(self._mascot.x - self._sourceBox.x) / 100
        self._tween = SimpleTween(duration, QtCore.QEasingCurve.InOutQuad, _update, self._nextPhoto)
