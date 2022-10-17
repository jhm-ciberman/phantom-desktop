import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __
from ..Models import Image
from ..Widgets.PixmapDisplay import PixmapDisplay
from .LucyRichardsonDeconvolution import (PointSpreadFunction,
                                          ProgressiveDeblurTask)
from .SliderWithSpinBox import SliderWithSpinBox


class _PsfConfig(QtWidgets.QWidget):
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

    def psf(self) -> np.ndarray:
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

    def _onPsfChanged(self):
        self.onPsfChanged.emit(self.psf())


class GaussianPsfConfig(_PsfConfig):
    """
    Containst the options for a gaussian blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._sigma = SliderWithSpinBox(QtCore.Qt.Horizontal)
        self._sigma.setRange(0.5, 50)
        self._sigma.setSingleStep(0.1)
        self._sigma.setValue(3.0)
        self._sigma.setLabelText(__("Sigma"))
        self._sigma.valueChanged.connect(self._onConfigChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._sigma)

        self.setLayout(layout)
        self._onConfigChanged()

    def title(self) -> str:
        return __("Gaussian blur")

    @QtCore.Slot(float)
    def _onConfigChanged(self) -> None:
        value = self._sigma.value()
        self._psf = PointSpreadFunction.gaussian(value)
        self._onPsfChanged()


class MotionBlurPsfConfig(_PsfConfig):
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
        self._angle.valueChanged.connect(self._onConfigChanged)

        self._length = QtWidgets.QSpinBox()
        self._length.setRange(1, 100)
        self._length.setSingleStep(1)
        self._length.setValue(10)
        self._length.valueChanged.connect(self._onConfigChanged)

        self._width = QtWidgets.QSpinBox()
        self._width.setRange(1, 10)
        self._width.setSingleStep(1)
        self._width.setValue(1)
        self._width.valueChanged.connect(self._onConfigChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(__("Angle:"), self._angle)
        layout.addRow(__("Length:"), self._length)
        layout.addRow(__("Width:"), self._width)

        self.setLayout(layout)
        self._onConfigChanged()

    def title(self) -> str:
        return __("Motion blur")

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        angle = self._angle.value()
        length = self._length.value()
        width = self._width.value()
        self._psf = PointSpreadFunction.motion_blur(angle, length, width)
        self._onPsfChanged()


class BoxBlurPsfConfig(_PsfConfig):
    """
    Containst the options for a box blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._size = QtWidgets.QSpinBox()
        self._size.setRange(1, 100)
        self._size.setSingleStep(1)
        self._size.setValue(3.0)
        self._size.valueChanged.connect(self._onConfigChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(__("Size:"), self._size)
        self.setLayout(layout)
        self._onConfigChanged()

    def title(self) -> str:
        return __("Box blur")

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        self._psf = PointSpreadFunction.box_blur(int(self._size.value()))
        self._onPsfChanged()


class DiskBlurPsfConfig(_PsfConfig):
    """
    Containst the options for a disk blur psf
    """
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._size = SliderWithSpinBox(QtCore.Qt.Horizontal)
        self._size.setRange(0.5, 50)
        self._size.setSingleStep(0.1)
        self._size.setValue(3.0)
        self._size.setLabelText(__("Radius"))
        self._size.valueChanged.connect(self._onConfigChanged)

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(__("Size:"), self._size)
        self.setLayout(layout)
        self._onConfigChanged()

    def title(self) -> str:
        return __("Disk blur")

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        self._psf = PointSpreadFunction.disk_blur(self._size.value())
        self._onPsfChanged()


class CustomPsfConfig(_PsfConfig):
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
        self._scale.valueChanged.connect(self._onConfigChanged)

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

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        scale = self._scale.value() / 100.0
        # resizes the psf to the desired scale
        self._psf = cv2.resize(self._unscaledPsf, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        self._onPsfChanged()


class _PropertiesPanel(QtWidgets.QFrame):
    """
    A properties panel for the DeblurWindow that shows:
    - A combo box for selecting the type of the PSF
    - The options for that selected PSF.
    - At the bottom, a progress bar (to show the progress of the preview)
    - At the bottom, an image showing the current PSF in grayscale.
    """

    configChanged = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)

        self._psfType = QtWidgets.QComboBox()

        options = [
            GaussianPsfConfig(self),  # default
            MotionBlurPsfConfig(self),
            BoxBlurPsfConfig(self),
            DiskBlurPsfConfig(self),
            CustomPsfConfig(self),
        ]

        for option in options:
            self._psfType.addItem(option.title(), option)
            option.onPsfChanged.connect(self._onPsfChanged)

        self._psfType.setCurrentIndex(0)
        self._psfType.currentIndexChanged.connect(self._onPsfTypeChanged)

        self._stackWidget = QtWidgets.QStackedWidget()
        self._stackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._stackWidget.setContentsMargins(0, 10, 0, 0)
        for option in options:
            self._stackWidget.addWidget(option)

        self._iterations = QtWidgets.QSpinBox()
        self._iterations.setRange(1, 1000)
        self._iterations.setSingleStep(10)
        self._iterations.setValue(10)
        self._iterations.valueChanged.connect(self._onConfigChanged)

        iterationsHelpLabel = QtWidgets.QLabel(__("More iterations means better results, but takes longer."))
        iterationsHelpLabel.setWordWrap(True)
        iterationsHelpLabel.setStyleSheet("color: gray")

        self._progressBar = QtWidgets.QProgressBar()
        self._progressBar.setRange(0, 100)
        self._progressBar.setValue(0)
        self._progressBar.setFixedHeight(20)
        self._progressBar.setTextVisible(False)

        self._progressiveCheckBox = QtWidgets.QCheckBox(__("Progressive preview"))
        self._progressiveCheckBox.setChecked(True)

        self._psfImage = QtWidgets.QLabel()
        self._psfImage.setFixedSize(100, 100)
        self._psfImage.setScaledContents(False)
        self._psfImage.setAlignment(QtCore.Qt.AlignCenter)

        self._psfInfoLabel = QtWidgets.QLabel()
        self._psfInfoLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._psfInfoLabel.setFixedWidth(100)

        psfFrame = QtWidgets.QFrame()
        psfFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        psfFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        psfFrame.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        psfLayout = QtWidgets.QHBoxLayout()
        psfLayout.addWidget(self._psfImage)
        psfLayout.addWidget(self._psfInfoLabel)
        psfFrame.setLayout(psfLayout)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._psfType)
        layout.addWidget(self._stackWidget)
        layout.addStretch()
        layout.addWidget(QtWidgets.QLabel(__("Iterations:")))
        layout.addWidget(self._iterations)
        layout.addWidget(iterationsHelpLabel)
        layout.addWidget(self._progressiveCheckBox)
        layout.addSpacing(10)
        layout.addWidget(self._progressBar)
        layout.addWidget(psfFrame)

        self.setLayout(layout)

        self._onPsfTypeChanged()

    @QtCore.Slot()
    def _onPsfTypeChanged(self) -> None:
        self._stackWidget.setCurrentIndex(self._psfType.currentIndex())
        self._onPsfChanged()

    @QtCore.Slot()
    def _onPsfChanged(self) -> None:
        option = self._psfType.currentData()  # type: _PsfConfig
        qimage = option.psfImage()
        psf = option.psf()
        w, h = psf.shape
        qimage = qimage.scaled(
                self._psfImage.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.TransformationMode.FastTransformation)
        self._psfImage.setPixmap(QtGui.QPixmap.fromImage(qimage))

        sizeStr = "{}x{}".format(w, h)
        self._psfInfoLabel.setText(__("Kernel size:") + "\n" + sizeStr)
        self._onConfigChanged()
        self.configChanged.emit()

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        self.configChanged.emit()

    def psf(self) -> np.ndarray:
        option = self._psfType.currentData()  # type: _PsfConfig
        return option.psf()

    def iterations(self) -> int:
        return self._iterations.value()

    def progressive(self) -> bool:
        return self._progressiveCheckBox.isChecked()

    def setProgress(self, progress: int) -> None:
        self._progressBar.setValue(progress)


class DeblurWindow(QtWidgets.QWidget):
    """
    A window that allows the user to deblur an image.
    """

    # The preview is updated in a separate thread, but all Qt calls must be done in the main thread.
    # The ProgressiveDeblurTask uses callbacks that are executed in a
    # separate thread, so we use the Qt signal/slot mechanism because Qt guarantees that
    # signals are executed in the main thread. These signals are only used from inside the
    # class, so they are private.

    _taskPreviewCalled = QtCore.Signal(np.ndarray)

    _taskProgressCalled = QtCore.Signal()

    _taskFinishedCalled = QtCore.Signal()

    def __init__(self, image: Image) -> None:
        """
        Initializes the DeblurWindow class.

        Args:
            image (Image): The image to deblur.
        """

        super().__init__()

        self._image = image
        self._previewBuffer: np.ndarray = None
        self._previewProgress: float = 0.0

        self._deblurTask: ProgressiveDeblurTask = None

        self.setWindowTitle(str(image.display_name) + " - Phantom")
        self.setMinimumSize(800, 600)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # Left side: deblur preview, right side: deblur options
        self._imagePreview = PixmapDisplay()
        self._imagePreview.setStyleSheet("background-color: #f0f0f0;")
        self._imagePreview.setAutoFillBackground(True)
        self._imagePreview.setMinimumHeight(200)
        self._imagePreview.setMinimumWidth(200)
        self._imagePreview.setPixmap(self._image.get_pixmap())

        self._propertiesPanel = _PropertiesPanel()
        self._propertiesPanel.configChanged.connect(self._onConfigChanged)

        layout.addWidget(self._imagePreview)
        layout.addWidget(self._propertiesPanel)

        self._taskPreviewCalled.connect(self._onPreview)
        self._taskProgressCalled.connect(self._onProgress)
        self._taskFinishedCalled.connect(self._onFinished)

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        self._updatePreview()

    def _updatePreview(self) -> None:
        if self._deblurTask is not None:
            self._deblurTask.cancel()

        rawImage = self._image.get_pixels_rgb()
        rect = self._imagePreview.imageRect()
        dstW, dstH = rect.width(), rect.height()
        iterations = self._propertiesPanel.iterations()
        cycles = None if self._propertiesPanel.progressive() else 1
        psf = self._propertiesPanel.psf()

        self._deblurTask = ProgressiveDeblurTask(
            rawImage,
            (dstW, dstH),
            psf,
            cycles=cycles,
            num_iter=iterations,
            on_preview=self._onPreviewFromTask,
            on_progress=self._onProgressFromTask,
            on_finished=self._onFinishedFromTask,
        )
        self._deblurTask.start()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._deblurTask is not None:
            self._deblurTask.cancel()

    def _onPreviewFromTask(self, preview: np.ndarray, current: int, total: int) -> None:
        self._previewBuffer = preview
        self._taskPreviewCalled.emit(preview)

    def _onProgressFromTask(self, progress: float) -> None:
        self._previewProgress = progress
        self._taskProgressCalled.emit()

    def _onFinishedFromTask(self) -> None:
        self._taskFinishedCalled.emit()

    @QtCore.Slot(np.ndarray)
    def _onPreview(self, preview: np.ndarray) -> None:
        w, h = preview.shape[1], preview.shape[0]
        bytesPerLine = w * 3
        image = QtGui.QImage(preview.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image)
        self._imagePreview.setPixmap(pixmap)

    @QtCore.Slot()
    def _onProgress(self) -> None:
        self._propertiesPanel.setProgress(self._previewProgress * 100)

    @QtCore.Slot()
    def _onFinished(self) -> None:
        self._propertiesPanel.setProgress(100)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._updatePreview()
