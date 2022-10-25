import os
from typing import Any

from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from PySide6 import QtCore, QtWidgets, QtGui

from ..Application import Application
from ..l10n import __
from ..Models import Face, Image, Project, Rect
from ..Widgets.PixmapDisplay import PixmapDisplay
from ..Widgets.PropertiesTable import PropertiesTable


class _InspectorPixmapDisplay(PixmapDisplay):
    """
    A preview image that optionally draws rectangles over the faces in the image.
    """

    _rects: list[Rect] = []

    _defaultRectPen: QtGui.QPen = QtGui.QPen(QtCore.Qt.gray, 2)

    _selectedRectPen: QtGui.QPen = QtGui.QPen(QtCore.Qt.green, 2)

    _selectedRectIndex: int = -1

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._defaultRectPen.setCosmetic(True)  # This makes the pen width independent of the zoom level
        self._selectedRectPen.setCosmetic(True)

    def setRects(self, rects: list[Rect]):
        self._rects = rects
        self.update()

    def rects(self) -> list[Rect]:
        return self._rects

    def selectedRectIndex(self) -> int:
        return self._selectedRectIndex

    def setSelectedRectIndex(self, index: int):
        self._selectedRectIndex = index
        self.update()

    def paintEvent(self, event: QtCore.QEvent):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setTransform(self._imageToWidgetTransform)  # Rects are in image coordinate space
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for i, rect in enumerate(self._rects):
            pen = self._selectedRectPen if i == self._selectedRectIndex else self._defaultRectPen
            painter.setPen(pen)
            painter.drawRect(rect.x, rect.y, rect.width, rect.height)


class _InspectorPropertiesTable(PropertiesTable):
    """
    A properties table for displaying image metadata.
    """

    faceSelected = QtCore.Signal(Face)
    """Signal emitted when a face is selected in the table."""

    def inspectImageInfo(self, image: Image):
        pilImage = PILImage.open(image.path)
        self._printBasicInformation(image, pilImage)
        self._printHashes(image)
        self._printExif(pilImage)
        self._printFaceDetection(image)

    def _printBasicInformation(self, image: Image, pilImage: PILImage):
        self.addHeader(__("Basic Information"))
        fileSize = os.path.getsize(image.path)
        path = image.path
        original_path = image.original_path

        self.addRow(__("Filename"), os.path.basename(path))
        self.addRow(__("Folder"), os.path.dirname(path))
        if path != original_path and original_path is not None:
            self.addRow(__("Original Filename"), os.path.basename(original_path))
            self.addRow(__("Original Folder"), os.path.dirname(original_path))

        self.addRow(__("Image Width"), pilImage.width)
        self.addRow(__("Image Height"), pilImage.height)
        self.addRow(__("File Size"), self._humanizeBytes(fileSize))
        self.addRow(__("Image Format"), pilImage.format_description)
        self.addRow(__("Color Channels"), pilImage.mode)
        self.addRow(__("Animated"), self._bool(getattr(pilImage, "is_animated", False)))
        frames = getattr(pilImage, "n_frames", 1)
        if frames > 1:
            self.addRow(__("Number of Frames"), frames)

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

    def _printHashes(self, image: Image):
        self.addHeader(__("Hashes"))
        hashes = image.hashes
        if len(hashes) == 0:
            self.addInfo(__("No hashes available"))
        else:
            for hash_type, hash in hashes.items():
                self.addRow(hash_type.upper(), hash)

    def _printExif(self, pilImage: PILImage):
        self.addHeader(__("EXIF Data"))
        exif = self._getExif(pilImage)
        if (len(exif) == 0):
            self.addInfo(__("No EXIF data available."))
        else:
            for key, value in exif.items():
                self.addRow(key, value)

    def _printFaceDetection(self, image: Image):
        self.addHeader(__("Face detection"))
        count = len(image.faces)
        if not image._processed:
            self.addInfo(__("Waiting for processing..."))
        elif (count == 0):
            self.addInfo(__("No faces detected."))
        elif (count == 1):
            self.addInfo(__("1 face detected."))
            self._printFaces(image.faces)
        else:
            self.addInfo(__("{count} faces detected.", count=count))
            self._printFaces(image.faces)

    def _printFaces(self, faces: list[Face]):
        for face in faces:
            pixmap = face.get_avatar_pixmap(64)
            group = face.group
            name = group.name if group is not None else __("Unknown")
            name = name if name != "" else __("Unknown")
            self.addPixmapRow(name, pixmap, value=face)

    def inspectProjectInfo(self, project: Project):
        self.addHeader(__("Project Information"))
        self.addRow(__("Project Name"), project.name)
        self.addRow(__("Project Path"), project.path)
        self.addRow(__("Number of Images"), len(project.images))

        if project.is_portable:
            self.addRow(__("Portable Project"), __("Yes"))
            self.addInfo(__("Portable projects can be moved to another location or copied to another computer."))
        else:
            self.addRow(__("Portable Project"), __("No"))
            self.addInfo(__("Non-portable projects can only be opened on the computer they were created on."))

    def inspectImagesInfo(self, images: list[Image]):
        """
        Inspects multiple images.
        """
        count = len(images)
        if count == 1:
            self.inspectImageInfo(images[0])
            return

        label = __("Selected {count} images", count=count)
        self.addHeader(label)
        # print first 10 images
        for i in range(min(10, count)):
            self.addInfo(images[i].display_name)
        if count > 10:
            self.addInfo(__("And {count} more...", count=count - 10))

    def selectedValueChangedEvent(self, value: Any):
        if isinstance(value, Face):
            self.faceSelected.emit(value)
        else:
            self.faceSelected.emit(None)


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

        self._table = _InspectorPropertiesTable()
        self._table.faceSelected.connect(self._onFaceSelected)

        topLayout = QtWidgets.QVBoxLayout()
        topLayout.setContentsMargins(0, 0, 0, 0)

        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.setSpacing(0)
        topLayout.addLayout(buttonsLayout)

        self._openButton = QtWidgets.QPushButton(__("Open"))
        self._openButton.setIcon(QtGui.QIcon("res/img/photo_viewer.png"))
        self._openButton.clicked.connect(self._openButtonClicked)
        buttonsLayout.addWidget(self._openButton)

        self._facesRectsAreVisible: bool = True
        self._toggleShowFacesButton = QtWidgets.QPushButton(__("Show Faces"))
        self._toggleShowFacesButton.setIcon(QtGui.QIcon("res/img/face.png"))
        self._toggleShowFacesButton.clicked.connect(self._toggleShowFacesButtonClicked)
        buttonsLayout.addWidget(self._toggleShowFacesButton)

        self._pixmapDisplay = _InspectorPixmapDisplay()
        self._pixmapDisplay.setMinimumHeight(200)
        self.setMinimumWidth(200)
        previewFrame = QtWidgets.QFrame()
        previewFrame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        previewFrame.setStyleSheet("background-color: #e0e0e0;")
        previewFrameLayout = QtWidgets.QVBoxLayout()
        previewFrameLayout.setContentsMargins(0, 0, 0, 0)
        previewFrameLayout.addWidget(self._pixmapDisplay)
        previewFrame.setLayout(previewFrameLayout)
        topLayout.addWidget(previewFrame)

        topWidget = QtWidgets.QWidget()
        topWidget.setLayout(topLayout)

        splitter.addWidget(topWidget)
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
        count = len(images)
        self._openButton.setEnabled(count == 1)
        hasFaces = False
        if count == 1:
            hasFaces = len(images[0].faces) > 0
        self._toggleShowFacesButton.setEnabled(hasFaces)
        self._refreshTable()
        self._refreshPreview()

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages

    @QtCore.Slot()
    def _openButtonClicked(self):
        """
        Called when the user clicks the "Open" button.
        """
        if len(self._selectedImages) == 1:
            image = self._selectedImages[0]
            Application.projectManager().openImageExternally(image)

    @QtCore.Slot()
    def _toggleShowFacesButtonClicked(self):
        """
        Called when the user clicks the "Show Faces" button.
        """
        self._facesRectsAreVisible = not self._facesRectsAreVisible
        self._refreshPreview()

    def _refreshPreview(self):
        """
        Refreshes the image preview.
        """
        count = len(self._selectedImages)
        facesCount = len(self._selectedImages[0].faces) if count == 1 else 0
        facesButtonText = ""
        if facesCount == 0:
            facesButtonText = __("No faces found")
        else:
            facesButtonText = __("Hide Faces") if self._facesRectsAreVisible else __("Show Faces")
        self._toggleShowFacesButton.setText(facesButtonText)

        if count == 1:
            self._setDisplayImage(self._selectedImages[0])
        else:
            self._clearDisplayImage()

    def _refreshTable(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        # Clear the table
        self._table.clear()

        count = len(self._selectedImages)
        if count == 0:
            project = Application.workspace().project()
            self._table.inspectProjectInfo(project)
        elif count == 1:
            self._table.inspectImageInfo(self._selectedImages[0])
        else:
            self._table.inspectImagesInfo(self._selectedImages)

    def _clearDisplayImage(self):
        """
        Clears the image information.
        """
        self._pixmapDisplay.setPixmap(None)
        self._pixmapDisplay.setRects([])
        self._pixmapDisplay.setSelectedRectIndex(-1)

    def _setDisplayImage(self, image: Image):
        """
        Sets the image to display.
        """
        self._pixmapDisplay.setPixmap(image.get_pixmap())
        rects = [face.aabb for face in image.faces] if self._facesRectsAreVisible else []
        self._pixmapDisplay.setRects(rects)

    @QtCore.Slot(Face)
    def _onFaceSelected(self, face: Face):
        """
        Called when the user selects a face.
        """
        if face is None:
            self._pixmapDisplay.setSelectedRectIndex(-1)
        else:
            faces = face.image.faces
            index = faces.index(face) if face in faces else -1
            self._pixmapDisplay.setSelectedRectIndex(index)
