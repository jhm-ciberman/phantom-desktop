import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __
from ..Models import Image
from ..Widgets.PixmapDisplay import PixmapDisplay
from ..Widgets.PixmapPointsDisplay import PixmapPointsDisplay
from .PerspectiveTransform import perspective_transform


class PerspectiveWindow(QtWidgets.QWidget):
    def __init__(self, image: Image) -> None:
        super().__init__()

        self._image = image
        # Initialize as 1x1 RGBA
        self._previewBuffer = np.zeros((1, 1, 4), dtype=np.uint8)  # type: cv2.Mat

        self._rotationIndex = 0
        self._points = []  # type: list[(int, int)]

        self.setWindowTitle(str(image.display_name) + " - Phantom")
        self.setMinimumSize(800, 600)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)
        splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(splitter)

        # Left side: points editor
        self._editor = PixmapPointsDisplay()
        self._editor.setAutoFillBackground(True)
        self._editor.setStyleSheet("background-color: #F00;")
        self._editor.setMinimumHeight(200)
        self._editor.setMinimumWidth(200)
        self._editor.setPixmap(self._image.get_pixmap())
        self._editor.pointsChanged.connect(self._onPointsChanged)
        self._editor.finished.connect(self._onPointsFinished)

        # right side: image result preview
        self._imagePreview = PixmapDisplay()
        self._imagePreview.setStyleSheet("background-color: #f0f0f0;")
        self._imagePreview.setAutoFillBackground(True)
        self._imagePreview.setMinimumHeight(200)
        self._imagePreview.setMinimumWidth(200)
        self._imagePreview.setPixmap(self._image.get_pixmap())
        self._imagePreview.imageRectChanged.connect(self._onPreviewRectChanged)

        splitter.addWidget(self._editor)
        splitter.addWidget(self._imagePreview)

        optionsFrame = QtWidgets.QFrame()
        optionsFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        optionsFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        optionsFrame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        optionsFrame.setMinimumWidth(200)
        optionsFrame.setMaximumWidth(400)

        formLayout = QtWidgets.QFormLayout()
        formLayout.setContentsMargins(10, 10, 10, 10)
        optionsFrame.setLayout(formLayout)

        layout.addWidget(optionsFrame)

        self._outputWidth = self._createSpinBox(min=1, max=10000, value=image.width, step=1, suffix="px")
        self._outputHeight = self._createSpinBox(min=1, max=10000, value=image.height, step=1, suffix="px")

        self._interpolationMode = QtWidgets.QComboBox()
        options = [
            (__("@interpolation_modes.nearest"), cv2.INTER_NEAREST),
            (__("@interpolation_modes.linear"), cv2.INTER_LINEAR),  # default
            (__("@interpolation_modes.area"), cv2.INTER_AREA),
            (__("@interpolation_modes.cubic"), cv2.INTER_CUBIC),
            (__("@interpolation_modes.lanczos4"), cv2.INTER_LANCZOS4)
        ]
        for name, value in options:
            self._interpolationMode.addItem(name, value)
        self._interpolationMode.setCurrentIndex(1)

        self._rotationModeSmart = QtWidgets.QToolButton()
        self._rotationModeSmart.setText(__("Smart"))
        self._rotationModeSmart.setCheckable(True)
        self._rotationModeSmart.setChecked(True)
        self._rotationModeSmart.clicked.connect(self._onRotationModeChanged)

        self._rotateCCW = QtWidgets.QPushButton(__("Rotate CCW"))
        self._rotateCW = QtWidgets.QPushButton(__("Rotate CW"))
        self._rotateCCW.clicked.connect(self._onRotateCCW)
        self._rotateCW.clicked.connect(self._onRotateCW)

        rotationLayout = QtWidgets.QHBoxLayout()
        rotationLayout.addWidget(self._rotationModeSmart)
        rotationLayout.addWidget(self._rotateCCW)
        rotationLayout.addWidget(self._rotateCW)

        aspectRatios = [
            (__("@aspect_ratios.custom"), None),
            (__("@aspect_ratios.original"), image.width / image.height),
            (__("@aspect_ratios.square"), 1),
            (__("@aspect_ratios.4_3"), 4 / 3),
            (__("@aspect_ratios.16_9"), 16 / 9),
            (__("@aspect_ratios.16_10"), 16 / 10),
            (__("@aspect_ratios.21_9"), 21 / 9),
            (__("@aspect_ratios.2_1"), 2 / 1),
            (__("@aspect_ratios.3_2"), 3 / 2),
            (__("@aspect_ratios.a4"), 210 / 297),
            (__("@aspect_ratios.letter"), 8.5 / 11),
            (__("@aspect_ratios.business_card"), 3.5 / 2),
            (__("@aspect_ratios.credit_card"), 3.375 / 2.125),
            (__("@aspect_ratios.legal"), 8.5 / 14),
            (__("@aspect_ratios.tabloid"), 11 / 17),
            (__("@aspect_ratios.ledger"), 17 / 11),
            (__("@aspect_ratios.executive"), 7.25 / 10.5),
            (__("@aspect_ratios.postcard"), 4 / 6),
            (__("@aspect_ratios.double_postcard"), 5 / 4),
        ]

        self._aspectRatio = QtWidgets.QComboBox()
        for name, ratio in aspectRatios:
            self._aspectRatio.addItem(name, ratio)

        formLayout.addRow(__("Aspect ratio"), self._aspectRatio)
        formLayout.addRow(__("Output width"), self._outputWidth)
        formLayout.addRow(__("Output height"), self._outputHeight)
        formLayout.addRow(__("Interpolation Mode"), self._interpolationMode)
        formLayout.addRow(__("Rotation"), rotationLayout)

        self._aspectRatio.currentIndexChanged.connect(self._onPreviewConfigChanged)
        self._interpolationMode.currentIndexChanged.connect(self._onPreviewConfigChanged)
        self._outputWidth.valueChanged.connect(self._onPreviewConfigChanged)
        self._outputHeight.valueChanged.connect(self._onPreviewConfigChanged)

        self._onPreviewConfigChanged()

    @QtCore.Slot()
    def _onPointsChanged(self) -> None:
        if self._editor.hasFinished():
            self._recomputePoints()
            self._updatePreview()

    @QtCore.Slot()
    def _onPointsFinished(self) -> None:
        self._recomputePoints()
        self._updatePreview()

    @QtCore.Slot()
    def _onPreviewConfigChanged(self) -> None:
        isCustomAspect = self._aspectRatio.currentData() is None
        self._outputHeight.setEnabled(isCustomAspect)
        self._updatePreview()

    @QtCore.Slot(QtCore.QRect)
    def _onPreviewRectChanged(self, rect: QtCore.QRect) -> None:
        self._updatePreview()

    def _updatePreview(self) -> None:
        if self._points is None or len(self._points) < 4:
            return

        aspectRatio = self._aspectRatio.currentData()
        if aspectRatio is None:
            aspectRatio = self._outputWidth.value() / self._outputHeight.value()
        w = min(self._outputWidth.value(), self._imagePreview.width())
        h = int(w / aspectRatio)
        previewShape = (h, w, 4)
        if self._previewBuffer.shape != previewShape:
            self._previewBuffer = np.zeros(previewShape, dtype=np.uint8)

        interpolation = self._interpolationMode.currentData()
        perspective_transform(self._image.get_pixels_rgba(), self._previewBuffer, self._points, interpolation)

        image = QtGui.QImage(self._previewBuffer.data, w, h, QtGui.QImage.Format.Format_RGBA8888)
        pixmap = QtGui.QPixmap.fromImage(image)
        self._imagePreview.setPixmap(pixmap)

    def _createSpinBox(self, min: int, max: int, value: int, step: int, suffix: str) -> QtWidgets.QSpinBox:
        spinBox = QtWidgets.QSpinBox()
        spinBox.setRange(min, max)
        spinBox.setValue(value)
        spinBox.setSingleStep(step)
        spinBox.setSuffix(suffix)
        return spinBox

    def _isClockwise(self, points: list) -> bool:
        """Returns True if the points are in clockwise order"""
        x1, y1 = points[0]
        x2, y2 = points[1]
        x3, y3 = points[2]
        return (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1) > 0

    def _indexOfTopLeftCorner(self, points: list) -> int:
        """Returns the index of the top left corner of the quadrilateral"""
        minx = min(points, key=lambda p: p[0])[0]
        miny = min(points, key=lambda p: p[1])[1]
        for i, (x, y) in enumerate(points):
            if x == minx and y == miny:
                return i
        return 0

    def _recomputePoints(self) -> None:
        points = [(p.x(), p.y()) for p in self._editor.points()]
        if len(points) < 4:
            return

        if not self._isClockwise(points):
            points = list(reversed(points))

        if self._rotationModeSmart.isChecked():
            self._rotationIndex = self._indexOfTopLeftCorner(points)

        self._points = points[self._rotationIndex:] + points[:self._rotationIndex]

    def _rotate(self, direction: int) -> None:
        self._rotationModeSmart.setChecked(False)
        self._rotationIndex = (self._rotationIndex - direction) % 4
        self._recomputePoints()
        self._updatePreview()

    @QtCore.Slot()
    def _onRotateCCW(self) -> None:
        self._rotate(-1)

    @QtCore.Slot()
    def _onRotateCW(self) -> None:
        self._rotate(1)

    @QtCore.Slot()
    def _onRotationModeChanged(self) -> None:
        if self._rotationModeSmart.isChecked():
            self._recomputePoints()
        self._updatePreview()
