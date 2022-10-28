import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ..ShellWindow import NavigationPage

from ..Application import Application
from ..l10n import __
from ..Models import Image
from ..Widgets.BussyModal import BussyModal
from ..Widgets.PixmapDisplay import PixmapDisplay
from .LucyRichardsonDeconvolution import (LucyRichardsonDeconvolution,
                                          ProgressiveDeblurTask)
from .PsfConfig import (BoxBlurPsfConfig, CustomPsfConfig, DiskBlurPsfConfig,
                        GaussianPsfConfig, MotionBlurPsfConfig, PsfConfig)


class _PropertiesPanel(QtWidgets.QFrame):
    """
    A properties panel for the DeblurWindow that shows:
    - A combo box for selecting the type of the PSF
    - The options for that selected PSF.
    - A button to reset the PSF to its default values
    - At the bottom, a progress bar (to show the progress of the preview)
    - At the bottom, an image showing the current PSF in grayscale.
    """

    configChanged = QtCore.Signal()
    """Raised when the psf type or settings have been modified"""

    isComparingChanged = QtCore.Signal(bool)
    """Raised when the compare image is enabled or disabled"""

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)

        self._psfType = QtWidgets.QComboBox()

        self._psfOptions: list[PsfConfig] = [
            GaussianPsfConfig(self),  # default
            MotionBlurPsfConfig(self),
            BoxBlurPsfConfig(self),
            DiskBlurPsfConfig(self),
            CustomPsfConfig(self),
        ]

        for option in self._psfOptions:
            self._psfType.addItem(option.title(), option)
            option.onPsfChanged.connect(self._onPsfChanged)

        self._psfType.setCurrentIndex(0)
        self._psfType.currentIndexChanged.connect(self._onPsfTypeChanged)

        self._stackWidget = QtWidgets.QStackedWidget()
        self._stackWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._stackWidget.setContentsMargins(0, 10, 0, 0)
        for option in self._psfOptions:
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

        self._isComparing = False
        self._compareButton = QtWidgets.QPushButton(__("Compare"))
        self._compareButton.setIcon(QtGui.QIcon("res/img/image_compare.png"))
        self._compareButton.setToolTip(__("Hold pressed to compare the result with the original image"))
        self._compareButton.setIconSize(QtCore.QSize(20, 20))
        # When the button is pressed we raise the isComparingChanged event.
        # When the button is released we send it again to raise the event
        self._compareButton.pressed.connect(self._onIsComparingChanged)
        self._compareButton.released.connect(self._onIsComparingChanged)

        checkBoxAndCompareLayout = QtWidgets.QHBoxLayout()
        checkBoxAndCompareLayout.addWidget(self._progressiveCheckBox, 1)
        checkBoxAndCompareLayout.setSpacing(10)
        checkBoxAndCompareLayout.addWidget(self._compareButton, 0)

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

        self.saveButton = QtWidgets.QPushButton(
                QtGui.QIcon("res/img/image_save.png"), __("Export Image"))
        self.saveButton.setIconSize(QtCore.QSize(32, 32))

        self.saveAndAddToProjectButton = QtWidgets.QPushButton(
                QtGui.QIcon("res/img/collection.png"), __("Export and add to project"))
        self.saveAndAddToProjectButton.setIconSize(QtCore.QSize(32, 32))

        self._resetButton = QtWidgets.QPushButton(
                QtGui.QIcon("res/img/reset.png"), __("Reset to defaults"))
        self._resetButton.setIconSize(QtCore.QSize(32, 32))
        self._resetButton.clicked.connect(self._onReset)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._psfType)
        layout.addWidget(self._stackWidget)
        layout.addStretch()
        layout.addWidget(QtWidgets.QLabel(__("Iterations:")))
        layout.addWidget(self._iterations)
        layout.addWidget(iterationsHelpLabel)
        layout.addLayout(checkBoxAndCompareLayout)
        layout.addSpacing(10)
        layout.addWidget(self._progressBar)
        layout.addWidget(psfFrame)
        layout.addSpacing(10)
        layout.addWidget(self._resetButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.saveAndAddToProjectButton)

        self.setLayout(layout)

        self._isResetting = False
        self._onReset()

    @QtCore.Slot()
    def _onPsfTypeChanged(self) -> None:
        self._stackWidget.setCurrentIndex(self._psfType.currentIndex())
        self._onPsfChanged()

    @QtCore.Slot()
    def _onIsComparingChanged(self) -> None:
        self._isComparing = self._compareButton.isDown()
        self.isComparingChanged.emit(self._isComparing)

    @QtCore.Slot()
    def _onPsfChanged(self) -> None:
        option = self._psfType.currentData()  # type: PsfConfig
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
        if not self._isResetting:
            self.configChanged.emit()

    @QtCore.Slot()
    def _onReset(self) -> None:
        self._isResetting = True
        self._iterations.setValue(50)
        self._progressiveCheckBox.setChecked(True)
        for option in self._psfOptions:
            option.reset()
        self._psfType.setCurrentIndex(0)
        self._isResetting = False
        self._onConfigChanged()

    def psf(self) -> np.ndarray:
        option = self._psfType.currentData()  # type: PsfConfig
        return option.psf()

    def iterations(self) -> int:
        return self._iterations.value()

    def progressive(self) -> bool:
        return self._progressiveCheckBox.isChecked()

    def setProgress(self, progress: int) -> None:
        self._progressBar.setValue(progress)


class DeblurPage(NavigationPage):
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

        self.setWindowTitle(image.display_name)
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

        self._originalPreview = PixmapDisplay()
        self._originalPreview.setStyleSheet("background-color: #f0f0f0;")
        self._originalPreview.setAutoFillBackground(True)
        self._originalPreview.setMinimumHeight(200)
        self._originalPreview.setMinimumWidth(200)
        self._originalPreview.setPixmap(self._image.get_pixmap())

        self._leftSide = QtWidgets.QStackedLayout()
        self._leftSide.addWidget(self._imagePreview)
        self._leftSide.addWidget(self._originalPreview)
        self._leftSide.setCurrentIndex(0)

        leftSideFrame = QtWidgets.QFrame()
        leftSideFrame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        leftSideFrame.setLayout(self._leftSide)

        self._propertiesPanel = _PropertiesPanel()
        self._propertiesPanel.configChanged.connect(self._onConfigChanged)
        self._propertiesPanel.saveButton.clicked.connect(self._onSaveButtonClicked)
        self._propertiesPanel.saveAndAddToProjectButton.clicked.connect(self._onSaveAndAddToProjectButtonClicked)
        self._propertiesPanel.isComparingChanged.connect(self._onComparingChanged)

        layout.addWidget(leftSideFrame, 1)
        layout.addWidget(self._propertiesPanel, 0)

        self._taskPreviewCalled.connect(self._onPreview)
        self._taskProgressCalled.connect(self._onProgress)
        self._taskFinishedCalled.connect(self._onFinished)

    @QtCore.Slot()
    def _onConfigChanged(self) -> None:
        self._updatePreview()

    @QtCore.Slot()
    def _onComparingChanged(self, comparing: bool):
        self._leftSide.setCurrentIndex(1 if comparing else 0)

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

    def _makeFinalImage(self) -> Image:
        rawImage = self._image.get_pixels_rgb()
        rect = self._imagePreview.imageRect()
        dstW, dstH = rect.width(), rect.height()
        iterations = self._propertiesPanel.iterations()
        psf = self._propertiesPanel.psf()

        modal = BussyModal(self, title=__("Deblurring Image"), subtitle=__("Working..."))
        result: Image = None

        def onProgress(current: int, total: int) -> None:
            percentStr = "{:.0f}%".format(current / total * 100)
            modal.setSubtitle(__("Working...") + " " + percentStr)

        def workerThread():
            nonlocal rawImage, dstW, dstH, iterations, psf, result
            lrd = LucyRichardsonDeconvolution(rawImage, psf, num_iter=iterations)
            raw_rgb = lrd.run(on_progress=onProgress)
            raw_rgba = cv2.cvtColor(raw_rgb, cv2.COLOR_RGB2RGBA)
            result = Image(raw_rgba=raw_rgba)

        modal.exec(workerThread)

        if result is None:
            raise Exception("Deblur task failed")
        return result

    def _exportAndClose(self, addToProject: bool) -> None:
        if self._deblurTask is not None:
            self._deblurTask.cancel()

        image = Application.projectManager().exportImageLazy(
                self, self._makeFinalImage, addToProject=addToProject)

        if image is not None:
            self.close()

    @QtCore.Slot()
    def _onSaveButtonClicked(self) -> None:
        self._exportAndClose(False)

    @QtCore.Slot()
    def _onSaveAndAddToProjectButtonClicked(self) -> None:
        self._exportAndClose(True)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._updatePreview()
