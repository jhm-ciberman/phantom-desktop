import os

from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from PySide6 import QtCore, QtWidgets

from ..Application import Application
from ..l10n import __
from ..Models import Image, Project
from ..Widgets.PixmapDisplay import PixmapDisplay
from ..Widgets.PropertiesTable import PropertiesTable


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

        splitter = QtWidgets.QSplitter()
        splitter.setContentsMargins(0, 0, 0, 0)
        splitter.setOrientation(QtCore.Qt.Vertical)

        self._table = PropertiesTable()

        self._pixmapDisplay = PixmapDisplay()
        self._pixmapDisplay.setMinimumHeight(200)
        self.setMinimumWidth(200)

        previewFrame = QtWidgets.QFrame()
        previewFrame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        previewFrame.setStyleSheet("background-color: #e0e0e0;")
        previewFrameLayout = QtWidgets.QVBoxLayout()
        previewFrameLayout.setContentsMargins(0, 0, 0, 0)
        previewFrameLayout.addWidget(self._pixmapDisplay)
        previewFrame.setLayout(previewFrameLayout)

        splitter.addWidget(previewFrame)
        splitter.addWidget(self._table)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.setLayout(layout)

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

    def _humanizeBytes(self, bytes: int) -> str:
        """
        Converts a number of bytes to a human-readable string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(bytes) < 1024.0:
                return "%3.1f %s" % (bytes, unit)
            bytes /= 1024.0
        return "%.1f %s" % (bytes, "YB")

    def _refreshInfo(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        # Clear the table
        self._table.clear()

        selected_count = len(self._selectedImages)
        if selected_count == 0:
            self._pixmapDisplay.setPixmap(None)
            self._printProjectInfo()
        elif selected_count == 1:
            image = self._selectedImages[0]
            self._inspectImage(image)
        else:
            self._pixmapDisplay.setPixmap(None)
            label = __("Selected {count} images", count=selected_count)
            self._table.addHeader(label)
            # print first 10 images
            for i in range(min(10, selected_count)):
                self._table.addInfo(self._selectedImages[i].display_name)
            if selected_count > 10:
                self._table.addInfo(__("And {count} more...", count=selected_count - 10))

    def _inspectImage(self, image: Image):  # noqa: C901
        self._pixmapDisplay.setPixmap(image.get_pixmap())

        pilImage = PILImage.open(image.path)
        self._printBasicInformation(image, pilImage)
        self._printHashes(image)
        self._printExif(pilImage)
        self._printFaceDetection(image)

    def _printBasicInformation(self, image: Image, pilImage: PILImage):
        self._table.addHeader(__("Basic Information"))
        fileSize = os.path.getsize(image.path)
        path = image.path
        original_path = image.original_path

        self._table.addRow(__("Filename"), os.path.basename(path))
        self._table.addRow(__("Folder"), os.path.dirname(path))
        if path != original_path:
            self._table.addRow(__("Original Filename"), os.path.basename(original_path))
            self._table.addRow(__("Original Folder"), os.path.dirname(original_path))

        self._table.addRow(__("Image Width"), pilImage.width)
        self._table.addRow(__("Image Height"), pilImage.height)
        self._table.addRow(__("File Size"), self._humanizeBytes(fileSize))
        self._table.addRow(__("Image Format"), pilImage.format_description)
        self._table.addRow(__("Color Channels"), pilImage.mode)
        self._table.addRow(__("Animated"), self._bool(getattr(pilImage, "is_animated", False)))
        frames = getattr(pilImage, "n_frames", 1)
        if frames > 1:
            self._table.addRow(__("Number of Frames"), frames)

    def _printHashes(self, image: Image):
        self._table.addHeader(__("Hashes"))
        hashes = image.hashes
        if len(hashes) == 0:
            self._table.addInfo(__("No hashes available"))
        else:
            for hash_type, hash in hashes.items():
                self._table.addRow(hash_type.upper(), hash)

    def _printExif(self, pilImage: PILImage):
        self._table.addHeader(__("EXIF Data"))
        exif = self._getExif(pilImage)
        if (len(exif) == 0):
            self._table.addInfo(__("No EXIF data available."))
        else:
            for key, value in exif.items():
                self._table.addRow(key, value)

    def _printFaceDetection(self, image: Image):
        self._table.addHeader(__("Face detection"))
        count = len(image.faces)
        if not image._processed:
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

    def _printProjectInfo(self):
        project: Project = Application.workspace().project()

        self._table.addHeader(__("Project Information"))
        self._table.addRow(__("Project Name"), project.name)
        self._table.addRow(__("Project Path"), project.path)
        self._table.addRow(__("Number of Images"), len(project.images))

        if project.is_portable:
            self._table.addRow(__("Portable Project"), __("Yes"))
            self._table.addInfo(__("Portable projects can be moved to another location or copied to another computer."))
        else:
            self._table.addRow(__("Portable Project"), __("No"))
            self._table.addInfo(__("Non-portable projects can only be opened on the computer they were created on."))
