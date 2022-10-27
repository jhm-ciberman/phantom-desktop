import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __
from .LucyRichardsonDeconvolution import PointSpreadFunction
from .SliderWithSpinBox import SliderWithSpinBox


class PsfConfig(QtWidgets.QWidget):
    """
    Abstract class for deblur options
    """
    onPsfChanged = QtCore.Signal(np.ndarray)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._psf = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self._psfImagePadding = 1  # Padding around the PSF image to make it easier to see
        self._isResetting = False

    def psf(self) -> np.ndarray:
        if self._psf is None:
            self._psf = self._createPsfCore()
        return self._psf

    def psfImage(self) -> QtGui.QImage:
        psf = self.psf()
        psfImg = PointSpreadFunction.to_grayscale(psf)
        if self._psfImagePadding > 0:
            psfImg = np.pad(psfImg, self._psfImagePadding, mode="constant", constant_values=0)
        shape = psfImg.shape
        w, h, bytesPerLine = shape[1], shape[0], shape[1]
        return QtGui.QImage(psfImg.data, w, h, bytesPerLine, QtGui.QImage.Format_Grayscale8)

    def title(self) -> str:
        raise NotImplementedError()

    def reset(self):
        self._isResetting = True
        self._resetCore()
        self._isResetting = False
        self._onPsfChanged()

    @QtCore.Slot()
    def _onPsfChanged(self):
        if not self._isResetting:
            self._psf = None
            self.onPsfChanged.emit(self.psf())

    def _createPsfCore(self) -> np.ndarray:
        raise NotImplementedError()

    def _resetCore(self):
        raise NotImplementedError()


class GaussianPsfConfig(PsfConfig):
    """
    Containst the options for a gaussian blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._sigma = SliderWithSpinBox(QtCore.Qt.Horizontal)
        self._sigma.setRange(0.5, 50)
        self._sigma.setSingleStep(0.1)
        self._sigma.setLabelText(__("Sigma"))
        self._sigma.valueChanged.connect(self._onPsfChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._sigma)

        self.setLayout(layout)
        self.reset()

    def title(self) -> str:
        return __("Gaussian blur")

    def _createPsfCore(self) -> np.ndarray:
        return PointSpreadFunction.gaussian(self._sigma.value())

    def _resetCore(self):
        self._sigma.setValue(3.0)


class MotionBlurPsfConfig(PsfConfig):
    """
    Containst the options for a motion blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._angle = QtWidgets.QDial(self)
        self._angle.setWrapping(True)
        self._angle.setNotchesVisible(True)
        self._angle.setRange(0, 360)
        self._angle.setSingleStep(1)
        self._angle.valueChanged.connect(self._onPsfChanged)

        self._length = QtWidgets.QSpinBox()
        self._length.setRange(1, 100)
        self._length.setSingleStep(1)
        self._length.valueChanged.connect(self._onPsfChanged)

        self._width = QtWidgets.QSpinBox()
        self._width.setRange(1, 10)
        self._width.setSingleStep(1)
        self._width.valueChanged.connect(self._onPsfChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(__("Angle:"), self._angle)
        layout.addRow(__("Length:"), self._length)
        layout.addRow(__("Width:"), self._width)

        self.setLayout(layout)
        self.reset()

    def title(self) -> str:
        return __("Motion blur")

    def _createPsfCore(self) -> np.ndarray:
        angle = self._angle.value()
        length = self._length.value()
        width = self._width.value()
        return PointSpreadFunction.motion_blur(angle, length, width)

    def _resetCore(self):
        self._angle.setValue(0)
        self._length.setValue(10)
        self._width.setValue(1)


class BoxBlurPsfConfig(PsfConfig):
    """
    Containst the options for a box blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._size = QtWidgets.QSpinBox()
        self._size.setRange(1, 100)
        self._size.setSingleStep(1)
        self._size.valueChanged.connect(self._onPsfChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(__("Size:"), self._size)
        self.setLayout(layout)
        self.reset()

    def title(self) -> str:
        return __("Box blur")

    def _createPsfCore(self) -> np.ndarray:
        return PointSpreadFunction.box_blur(int(self._size.value()))

    def _resetCore(self):
        self._size.setValue(3)


class DiskBlurPsfConfig(PsfConfig):
    """
    Containst the options for a disk blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._size = SliderWithSpinBox(QtCore.Qt.Horizontal)
        self._size.setRange(0.5, 50)
        self._size.setSingleStep(0.1)
        self._size.setLabelText(__("Radius"))
        self._size.valueChanged.connect(self._onPsfChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(__("Size:"), self._size)
        self.setLayout(layout)
        self.reset()

    def title(self) -> str:
        return __("Disk blur")

    def _createPsfCore(self) -> np.ndarray:
        return PointSpreadFunction.disk_blur(self._size.value())

    def _resetCore(self):
        self._size.setValue(3.0)


class CustomPsfConfig(PsfConfig):
    """
    Contains the options for a custom psf. This option contains a button to open a file dialog to select a custom
    image to be used as a psf. It also shows the file path (with elipsis)
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        text = __("Select a grayscale image to use as kernel for the deconvolution")
        self._label = QtWidgets.QLabel(text)
        self._label.setWordWrap(True)
        self._label.setAlignment(QtCore.Qt.AlignLeft)

        self._filePath = QtWidgets.QLineEdit()
        self._filePath.setReadOnly(True)
        self._filePath.setPlaceholderText(__("No file selected"))
        self._filePath.setFrame(False)

        self._selectFileButton = QtWidgets.QPushButton(__("Select file"))
        self._selectFileButton.clicked.connect(self._onSelectFile)

        self._scale = QtWidgets.QDoubleSpinBox()
        self._scale.setRange(1, 300)
        self._scale.setSingleStep(1)
        self._scale.setValue(100.0)
        self._scale.setEnabled(False)
        self._scale.setSuffix("%")
        self._scale.valueChanged.connect(self._onPsfChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(self._label)
        layout.addRow(self._filePath)
        layout.addRow(self._selectFileButton)
        spacer = QtWidgets.QSpacerItem(0, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)
        layout.addRow(__("Scale:"), self._scale)
        self.setLayout(layout)

        self._psf = np.array([[1]])  # default psf
        self._unscaledPsf = self._psf

        self.reset()

    def title(self) -> str:
        return __("Custom")

    @QtCore.Slot()
    def _onSelectFile(self) -> None:
        title = __("Select Kernel")
        filters = __("Image files") + " (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, "", filters)
        if filePath:
            self._filePath.setText(filePath)
            self._psf = PointSpreadFunction.from_file(filePath)
            self._unscaledPsf = self._psf
            self._scale.setEnabled(True)
            self._onConfigChanged()

    def _createPsfCore(self) -> np.ndarray:
        scale = self._scale.value() / 100.0
        # resizes the psf to the desired scale
        return cv2.resize(self._unscaledPsf, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    def _resetCore(self):
        self._filePath.setText("")
        self._scale.setEnabled(False)
        self._scale.setValue(100.0)
        self._psf = np.array([[1]])
        self._unscaledPsf = self._psf
