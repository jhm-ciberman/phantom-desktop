from typing import Any
from PySide6 import QtCore, QtWidgets
from .ImagePreview import ImagePreview
from .InfoProviders import ImageInfoProvider, MultiImageInfoProvider, ProjectInfoProvider

from ..Models import Face, Image
from ..Widgets.PropertiesTable import PropertiesTable


class InspectorPanel(QtWidgets.QWidget):
    """
    An abstract widget that displays a the properties of an image or a group of images.
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
        self._table.selectedValueChanged.connect(self._onTableSelectionChanged)

        self._preview = ImagePreview()
        splitter.addWidget(self._preview)
        splitter.addWidget(self._table)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.setLayout(layout)

    def setSelectedImages(self, images: list[Image]):
        """
        Sets the selected images.
        """
        self._selectedImages = images
        self._refresh()

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages

    def _refresh(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        count = len(self._selectedImages)
        if count == 0:
            ProjectInfoProvider().populate(self._table)
            self._preview.setImage(None)
        elif count == 1:
            image = self._selectedImages[0]
            ImageInfoProvider(image).populate(self._table)
            self._preview.setImage(image)
        else:
            MultiImageInfoProvider(self._selectedImages).populate(self._table)
            self._preview.setImage(None)

    @QtCore.Slot()
    def _onTableSelectionChanged(self, value: Any):
        """
        Called when the user selects a value in the table.
        """
        if isinstance(value, Face):
            self._preview.setSelectedFace(value)
        else:
            self._preview.setSelectedFace(None)
