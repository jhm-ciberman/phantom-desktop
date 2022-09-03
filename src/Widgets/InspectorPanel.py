from PySide6 import QtGui, QtCore, QtWidgets
from src.Image import Image
from .PixmapDisplay import PixmapDisplay
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

class InspectorPanel(QtWidgets.QWidget):
    """
    A widget that displays a the properties of an image or a group of images.
    """
    def __init__(self):
        """
        Initializes the InspectorPanel class.
        """
        super().__init__()

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self.setContentsMargins(0, 0, 0, 0)

        self._frame = QtWidgets.QFrame()
        self._frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self._frame.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self._frame.setContentsMargins(0, 0, 0, 0)
        self._frameLayout = QtWidgets.QFormLayout()
        self._frameLayout.setContentsMargins(10, 10, 10, 10)
        self._frame.setLayout(self._frameLayout)

        self._layout.addWidget(self._frame)

        self._pixmapDisplay = PixmapDisplay()
        self._pixmapDisplay.setMinimumHeight(200)
        self.setMinimumWidth(200)
        self._layout.addWidget(self._pixmapDisplay)
        
        self._selectedImages = []

    def setSelectedImages(self, images: list[Image]):
        """
        Sets the selected images.
        """
        self._selectedImages = images
        self._refresh_info()

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages

    def _get_exif(self, image: PILImage) -> dict[str, str]:
        """
        Gets the EXIF data from the image.
        """
        exif = {}
        info = image.getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif[decoded] = value

        return exif

    def _get_basic_info(self, image: PILImage) -> dict[str, str]:
        """
        Gets basic information about the image.
        """
        return {
            "Filename": image.filename,
            "Image Width": image.width,
            "Image Height": image.height,
            "Image Format": image.format,
            "Image Mode": image.mode,
            "Image is Animated": getattr(image, "is_animated", False),
            "Frames in Image": getattr(image, "n_frames", 1)
        }

    def _refresh_info(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        # delete all children in _frameLayout
        for i in reversed(range(self._frameLayout.count())):
            widget = self._frameLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        selected_count = len(self._selectedImages)
        if selected_count == 0:
            self._pixmapDisplay.setPixmap(None)
        elif selected_count == 1:
            image = self._selectedImages[0]
            self._pixmapDisplay.setPixmap(image.pixmap)

            pil_image = PILImage.open(image.path)

            basic_info = self._get_basic_info(pil_image)
            for key, value in basic_info.items():
                label = QtWidgets.QLabel(key)
                label.setStyleSheet("font-weight: bold; margin-right: 10px;")
                value_label = QtWidgets.QLabel(str(value))
                self._frameLayout.addRow(label, value_label)

            exif = self._get_exif(pil_image)
            if (len(exif) == 0):
                label = QtWidgets.QLabel("No EXIF data found.")
                label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #555;")
                self._frameLayout.addRow(label)
            else:
                label = QtWidgets.QLabel("EXIF Data")
                label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #555;")
                self._frameLayout.addRow(label)
                for key, value in exif.items():
                    label = QtWidgets.QLabel(key)
                    label.setStyleSheet("font-weight: bold; margin-right: 10px;")
                    value_label = QtWidgets.QLabel(str(value))
                    self._frameLayout.addRow(label, value_label)
        else:
            self._pixmapDisplay.setPixmap(None)
            label = QtWidgets.QLabel(str(selected_count) + " Images Selected")
            label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #555;")
            self._frameLayout.addRow(label)