from typing import Tuple

import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..ShellWindow import NavigationPage
from ..Application import Application
from ..l10n import __
from ..Models import Image
from ..Widgets.PixmapDisplay import PixmapDisplay
from .PerspectiveTransform import perspective_transform
from .PixmapPointsDisplay import PixmapPointsDisplay


class PerspectivePage(QtWidgets.QWidget, NavigationPage):
    def __init__(self, image: Image) -> None:
        super().__init__()

        self._image = image
        # Initialize as 1x1 RGBA
        self._previewBuffer = np.zeros((1, 1, 4), dtype=np.uint8)  # type: cv2.Mat

        self._rotationIndex = 0
        self._points = []  # type: list[(int, int)]

        self.setWindowTitle(image.display_name)
        self.setWindowIcon(QtGui.QIcon("res/img/correct_perspective.png"))
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
        rightColumn = QtWidgets.QSplitter()
        rightColumn.setOrientation(QtCore.Qt.Vertical)
        rightColumn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self._imagePreview = PixmapDisplay()
        self._imagePreview.setStyleSheet("background-color: #f0f0f0;")
        self._imagePreview.setAutoFillBackground(True)
        self._imagePreview.setMinimumHeight(200)
        self._imagePreview.setMinimumWidth(200)
        self._imagePreview.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self._imagePreview.setPixmap(self._image.get_pixmap())
        self._imagePreview.imageRectChanged.connect(self._onPreviewRectChanged)

        imagePreviewFrame = QtWidgets.QFrame()
        imagePreviewFrame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        imagePreviewFrame.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        imagePreviewFrame.setStyleSheet("background-color: #e0e0e0;")
        imagePreviewFrameLayout = QtWidgets.QVBoxLayout()
        imagePreviewFrameLayout.setContentsMargins(0, 0, 0, 0)
        imagePreviewFrame.setLayout(imagePreviewFrameLayout)
        imagePreviewFrameLayout.addWidget(self._imagePreview)

        optionsFrame = QtWidgets.QFrame()
        optionsFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        optionsFrame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        optionsFrame.setMinimumWidth(200)
        optionsFrameLayout = QtWidgets.QVBoxLayout()
        optionsFrameLayout.setContentsMargins(10, 10, 10, 10)
        optionsFrame.setLayout(optionsFrameLayout)

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
        self._rotationModeSmart.setText(__("Smart rotation"))
        self._rotationModeSmart.setIcon(QtGui.QIcon("res/img/idea.png"))
        self._rotationModeSmart.setIconSize(QtCore.QSize(32, 32))
        self._rotationModeSmart.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self._rotationModeSmart.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self._rotationModeSmart.setCheckable(True)
        self._rotationModeSmart.setChecked(True)
        self._rotationModeSmart.clicked.connect(self._onRotationModeChanged)

        self._rotateCCW = QtWidgets.QToolButton()
        self._rotateCCW.setIcon(QtGui.QIcon("res/img/rotate_left.png"))
        self._rotateCCW.setIconSize(QtCore.QSize(32, 32))
        self._rotateCCW.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self._rotateCCW.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self._rotateCCW.setText(__("Rotate CCW"))
        self._rotateCCW.clicked.connect(self._onRotateCCW)

        self._rotateCW = QtWidgets.QToolButton()
        self._rotateCW.setIcon(QtGui.QIcon("res/img/rotate_right.png"))
        self._rotateCW.setIconSize(QtCore.QSize(32, 32))
        self._rotateCW.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self._rotateCW.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self._rotateCW.setText(__("Rotate CW"))
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

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(__("Aspect ratio"), self._aspectRatio)
        formLayout.addRow(__("Output width"), self._outputWidth)
        formLayout.addRow(__("Output height"), self._outputHeight)
        formLayout.addRow(__("Rotation"), rotationLayout)
        formLayout.addRow(__("Interpolation Mode"), self._interpolationMode)

        exportSaveLayout = QtWidgets.QHBoxLayout()
        exportSaveLayout.addStretch()
        exportSaveLayout.setContentsMargins(0, 20, 0, 0)
        exportSaveLayout.setSpacing(10)

        self._saveButton = QtWidgets.QPushButton(
                QtGui.QIcon("res/img/image_save.png"), __("Export Image"))
        self._saveButton.clicked.connect(self._onSavePressed)
        self._saveButton.setIconSize(QtCore.QSize(32, 32))
        self._saveButton.setStyleSheet("padding: 5px 20px")
        exportSaveLayout.addWidget(self._saveButton)

        self._saveAndAddToProjectButton = QtWidgets.QPushButton(
                QtGui.QIcon("res/img/collection.png"), __("Export and add to project"))
        self._saveAndAddToProjectButton.clicked.connect(self._onSaveAndAddToProjectPressed)
        self._saveAndAddToProjectButton.setIconSize(QtCore.QSize(32, 32))
        self._saveAndAddToProjectButton.setStyleSheet("padding: 5px 20px")
        exportSaveLayout.addWidget(self._saveAndAddToProjectButton)

        optionsFrameLayout.addLayout(formLayout)
        optionsFrameLayout.addStretch()
        optionsFrameLayout.addLayout(exportSaveLayout)

        self._aspectRatio.currentIndexChanged.connect(self._onPreviewConfigChanged)
        self._interpolationMode.currentIndexChanged.connect(self._onPreviewConfigChanged)
        self._outputWidth.valueChanged.connect(self._onPreviewConfigChanged)
        self._outputHeight.valueChanged.connect(self._onPreviewConfigChanged)

        splitter.addWidget(self._editor)
        splitter.addWidget(rightColumn)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        rightColumn.addWidget(imagePreviewFrame)
        rightColumn.addWidget(optionsFrame)
        rightColumn.setCollapsible(0, False)
        rightColumn.setCollapsible(1, False)

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

    def _computeOutputShape(self) -> Tuple[int, int, int]:
        aspectRatio = self._aspectRatio.currentData()
        if aspectRatio is None:
            aspectRatio = self._outputWidth.value() / self._outputHeight.value()
        w = min(self._outputWidth.value(), self._imagePreview.width())
        h = int(w / aspectRatio)
        previewShape = (h, w, 4)
        return previewShape

    def _updatePreview(self) -> None:
        if self._points is None or len(self._points) < 4:
            return

        previewShape = self._computeOutputShape()
        if self._previewBuffer.shape != previewShape:
            self._previewBuffer = np.zeros(previewShape, dtype=np.uint8)

        interpolation = self._interpolationMode.currentData()
        perspective_transform(self._image.get_pixels_rgba(), self._previewBuffer, self._points, interpolation)

        w, h = previewShape[1], previewShape[0]
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

    def _createFinalImage(self) -> Image:
        if self._points is None or len(self._points) < 4:
            return

        interpolation = self._interpolationMode.currentData()
        outputShape = self._computeOutputShape()
        outputBuffer = np.zeros(outputShape, dtype=np.uint8)
        perspective_transform(self._image.get_pixels_rgba(), outputBuffer, self._points, interpolation)

        return Image(raw_rgba=outputBuffer)

    @QtCore.Slot()
    def _onSavePressed(self) -> None:
        image = self._createFinalImage()
        Application.projectManager().exportImage(self, image)

    @QtCore.Slot()
    def _onSaveAndAddToProjectPressed(self) -> None:
        image = self._createFinalImage()
        Application.projectManager().exportImage(self, image, addToProject=True)
