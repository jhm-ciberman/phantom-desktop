from PySide6 import QtGui, QtCore, QtWidgets
from .Image import Image
from .Widgets.PixmapDisplay import PixmapDisplay
import numpy as np
from .Services.DeblurFilter import DeblurFilter
import cv2


class DeblurWindow(QtWidgets.QWidget):
    def __init__(self, image: Image) -> None:
        super().__init__()

        self._image = image

        self._previewBuffer = np.zeros((1, 1, 4), dtype=np.uint8)  # type: cv2.Mat

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
        self._imagePreview.setPixmap(self._image.pixmap)

        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        frame.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        frame.setMinimumWidth(200)
        frame.setMinimumHeight(200)

        layout.addWidget(self._imagePreview)
        layout.addWidget(frame)

        # Deblur options
        optionsLayout = QtWidgets.QFormLayout()
        frame.setLayout(optionsLayout)

        # Deblur options: blur radius and iterations
        self._blurRadius = QtWidgets.QSpinBox()
        self._blurRadius.setMinimum(1)
        self._blurRadius.setMaximum(100)
        self._blurRadius.setValue(5)
        self._blurRadius.valueChanged.connect(self._onSettingsChanged)

        self._blurIterations = QtWidgets.QSpinBox()
        self._blurIterations.setMinimum(1)
        self._blurIterations.setMaximum(100)
        self._blurIterations.setValue(10)
        self._blurIterations.valueChanged.connect(self._onSettingsChanged)

        optionsLayout.addRow("Blur radius", self._blurRadius)
        optionsLayout.addRow("Iterations", self._blurIterations)

    @QtCore.Slot()
    def _onSettingsChanged(self) -> None:
        self._updatePreview()

    def _updatePreview(self) -> None:
        rawImage = self._image.raw_image
        srcW, srcH = self._image.width, self._image.height

        rect = self._imagePreview.imageRect()
        dstW, dstH = rect.width(), rect.height()
        previewShape = (dstH, dstW, 4)
        if self._previewBuffer.shape != previewShape:
            self._previewBuffer = np.zeros(previewShape, dtype=np.uint8)
            # draw the image into the buffer
            cv2.resize(rawImage, (dstW, dstH), self._previewBuffer, interpolation=cv2.INTER_AREA)

        scale = dstW / srcW
        sigmag = self._blurRadius.value() / scale
        # round to next odd number (> 0)
        sigmag = 1 if sigmag < 1 else int(sigmag) | 1
        iterations = self._blurIterations.value()

        print("srcW: {}, srcH: {}, dstW: {}, dstH: {}, scale: {}, sigmag: {}, iterations: {}"
              .format(srcW, srcH, dstW, dstH, scale, sigmag, iterations))

        result = DeblurFilter.lucy_richardson_deconv(self._previewBuffer, iterations, sigmag)

        image = QtGui.QImage(result.data, result.shape[1], result.shape[0], QtGui.QImage.Format_RGBA8888)
        pixmap = QtGui.QPixmap.fromImage(image)
        self._imagePreview.setPixmap(pixmap)
