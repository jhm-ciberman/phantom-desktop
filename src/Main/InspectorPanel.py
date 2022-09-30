from PySide6 import QtWidgets
from ..Widgets.PixmapDisplay import PixmapDisplay
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from ..Widgets.PropertiesTable import PropertiesTable
from ..Image import Image


class InspectorPanel(QtWidgets.QWidget):
    """
    A widget that displays a the properties of an image or a group of images.
    It shows the image itself, the basic information about the image, the EXIF data and the face detection results.
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

        self._table = PropertiesTable()
        self._layout.addWidget(self._table)

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
        self._refreshInfo()

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages

    def _getExif(self, image: PILImage) -> dict[str, str]:
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

    def _bool(self, value: bool) -> str:
        """
        Converts a boolean value to a string.
        """
        return "Yes" if value else "No"

    def _refreshInfo(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        # Clear the table
        self._table.clear()

        selected_count = len(self._selectedImages)
        if selected_count == 0:
            self._pixmapDisplay.setPixmap(None)
        elif selected_count == 1:
            image = self._selectedImages[0]
            self._inspectImage(image)
        else:
            self._pixmapDisplay.setPixmap(None)
            label = str(selected_count) + " Images Selected"
            self._table.addHeader(label)

    def _inspectImage(self, image: Image):
        self._pixmapDisplay.setPixmap(image.get_pixmap())

        pil_image = PILImage.open(image.full_path)

        self._table.addHeader("Basic Information")
        self._table.addRow("Filename", image.basename)
        self._table.addRow("Folder", image.folder_path)
        self._table.addRow("Image Width", pil_image.width)
        self._table.addRow("Image Height", pil_image.height)
        self._table.addRow("Image Format", pil_image.format_description)
        self._table.addRow("Color Channels", pil_image.mode)
        self._table.addRow("Animated", self._bool(getattr(pil_image, "is_animated", False)))
        frames = getattr(pil_image, "n_frames", 1)
        if frames > 1:
            self._table.addRow("Number of Frames", frames)

        self._table.addHeader("EXIF Data")
        exif = self._getExif(pil_image)
        if (len(exif) == 0):
            self._table.addInfo("No EXIF data available.")
        else:
            for key, value in exif.items():
                self._table.addRow(key, value)

        self._table.addHeader("Face detection")
        count = len(image.faces)
        if not image.processed:
            self._table.addInfo("Waiting for processing...")
        elif (count == 0):
            self._table.addInfo("No faces detected.")
        elif (count == 1):
            self._table.addInfo("1 face detected.")
            self._table.addRow("Confidence", image.faces[0].confidence)
        else:
            self._table.addInfo(str(count) + " faces detected.")
            for i, face in enumerate(image.faces):
                self._table.addRow(f"Face {i + 1} Confidence", face.confidence)
