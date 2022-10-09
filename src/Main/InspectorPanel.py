from PySide6 import QtWidgets
from ..Widgets.PixmapDisplay import PixmapDisplay
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from ..Widgets.PropertiesTable import PropertiesTable
from ..Models import Image
import hashlib
from src.l10n import __


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
        return __("Yes") if value else __("No")

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
            label = __("Selected {count} images", count=selected_count)
            self._table.addHeader(label)

    def _getHashes(self, image: Image) -> dict[str, str]:
        """
        Gets the hashes of the image.
        """
        bytes = image.read_file_bytes()

        hashes = {}
        hashes["md5"] = hashlib.md5(bytes).hexdigest()
        hashes["sha1"] = hashlib.sha1(bytes).hexdigest()
        hashes["sha256"] = hashlib.sha256(bytes).hexdigest()
        hashes["sha512"] = hashlib.sha512(bytes).hexdigest()

        return hashes

    def _inspectImage(self, image: Image):
        self._pixmapDisplay.setPixmap(image.get_pixmap())

        pil_image = PILImage.open(image.full_path)

        self._table.addHeader(__("Basic Information"))
        self._table.addRow(__("Filename"), image.basename)
        self._table.addRow(__("Folder"), image.folder_path)
        self._table.addRow(__("Image Width"), pil_image.width)
        self._table.addRow(__("Image Height"), pil_image.height)
        self._table.addRow(__("Image Format"), pil_image.format_description)
        self._table.addRow(__("Color Channels"), pil_image.mode)
        self._table.addRow(__("Animated"), self._bool(getattr(pil_image, "is_animated", False)))
        frames = getattr(pil_image, "n_frames", 1)
        if frames > 1:
            self._table.addRow(__("Number of Frames"), frames)

        self._table.addHeader(__("Hashes"))
        hashes = self._getHashes(image)
        for hash_type, hash in hashes.items():
            self._table.addRow(hash_type.upper(), hash)

        self._table.addHeader(__("EXIF Data"))
        exif = self._getExif(pil_image)
        if (len(exif) == 0):
            self._table.addInfo(__("No EXIF data available."))
        else:
            for key, value in exif.items():
                self._table.addRow(key, value)

        self._table.addHeader(__("Face detection"))
        count = len(image.faces)
        if not image.processed:
            self._table.addInfo(__("Waiting for processing..."))
        elif (count == 0):
            self._table.addInfo(__("No faces detected."))
        elif (count == 1):
            self._table.addInfo(__("1 face detected."))
            self._table.addRow(__("Confidence"), image.faces[0].confidence)
        else:
            self._table.addInfo(__("{count} faces detected.", count=count))
            for i, face in enumerate(image.faces):
                self._table.addRow(__("Face {index} Confidence", index=i + 1), face.confidence)
