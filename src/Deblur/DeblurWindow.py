from PySide6 import QtGui, QtCore, QtWidgets
from ..Models import Image
from ..Widgets.PixmapDisplay import PixmapDisplay
import numpy as np
from .LucyRichardsonDeconvolution import ProgressiveDeblurTask, PointSpreadFunction
from src.l10n import __


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

        self.setWindowTitle(str(image.basename) + " - Phantom")
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

        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        frame.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        frame.setMinimumWidth(200)
        frame.setMinimumHeight(200)

        layout.addWidget(self._imagePreview)
        layout.addWidget(frame)

        # Deblur options
        optionsLayout = QtWidgets.QFormLayout()
        frame.setLayout(optionsLayout)

        # Deblur options: blur radius
        self._blurRadius = QtWidgets.QSpinBox()
        self._blurRadius.setMinimum(1)
        self._blurRadius.setMaximum(100)
        self._blurRadius.setValue(5)
        self._blurRadius.valueChanged.connect(self._onSettingsChanged)

        # Deblur options: blur iterations
        self._blurIterations = QtWidgets.QSpinBox()
        self._blurIterations.setMinimum(1)
        self._blurIterations.setMaximum(5000)
        self._blurIterations.setValue(10)
        self._blurIterations.valueChanged.connect(self._onSettingsChanged)

        # Deblur options: progress bar
        self._progressBar = QtWidgets.QProgressBar()
        self._progressBar.setRange(0, 100)
        self._progressBar.setValue(0)

        optionsLayout.addRow(__("Blur radius"), self._blurRadius)
        optionsLayout.addRow(__("Iterations"), self._blurIterations)
        optionsLayout.addRow(self._progressBar)

        # self._simplePreviewLabel = QtWidgets.QLabel()
        # self._simplePreviewLabel.setPixmap(self._image.get_pixmap())
        # self._simplePreviewLabel.setAlignment(QtCore.Qt.AlignCenter)
        # self._simplePreviewLabel.setScaledContents(True)
        # self._simplePreviewLabel.setFixedSize(200, 200)
        # optionsLayout.addRow(__("Preview"), self._simplePreviewLabel)

        self._taskPreviewCalled.connect(self._onPreview)
        self._taskProgressCalled.connect(self._onProgress)
        self._taskFinishedCalled.connect(self._onFinished)

    @QtCore.Slot()
    def _onSettingsChanged(self) -> None:
        self._updatePreview()

    def _updatePreview(self) -> None:
        if self._deblurTask is not None:
            self._deblurTask.cancel()

        rawImage = self._image.get_pixels_rgb()
        rect = self._imagePreview.imageRect()
        dstW, dstH = rect.width(), rect.height()
        sigmag = self._blurRadius.value()
        iterations = self._blurIterations.value()
        psf = PointSpreadFunction.gaussian(sigmag)

        print(f"rawImage.shape = {rawImage.shape}")
        print(f"dstW = {dstW}, dstH = {dstH}")
        self._deblurTask = ProgressiveDeblurTask(
            rawImage,
            (dstW, dstH),
            psf,
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
        self._progressBar.setValue(self._previewProgress * 100)

    @QtCore.Slot()
    def _onFinished(self) -> None:
        self._progressBar.setValue(100)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._updatePreview()
