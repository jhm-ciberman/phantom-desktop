from PySide6 import QtCore, QtWidgets, QtGui

from ..Application import Application
from ..l10n import __
from ..Models import Face, Image
from ..Widgets.PixmapDisplay import PixmapDisplay


class _InspectorPixmapDisplay(PixmapDisplay):
    """
    A preview image that optionally draws rectangles over the faces in the image.
    """

    _faces: list[Face] = []

    _defaultFacePen: QtGui.QPen = QtGui.QPen(QtCore.Qt.gray, 2)

    _selectedFacePen: QtGui.QPen = QtGui.QPen(QtCore.Qt.green, 2)

    _highlightedFacePen: QtGui.QPen = QtGui.QPen(QtCore.Qt.red, 2)

    _selectedFace: Face = None

    _highlightedFace: Face = None

    _isShowingFaces: bool = True

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._defaultFacePen.setCosmetic(True)  # This makes the pen width independent of the zoom level
        self._selectedFacePen.setCosmetic(True)

    def setFaces(self, faces: list[Face]):
        self._faces = faces
        self.update()

    def faces(self) -> list[Face]:
        return self._faces

    def setSelectedFace(self, face: Face):
        self._selectedFace = face
        self.update()

    def selectedFace(self) -> Face:
        return self._selectedFace

    def setHighlightedFace(self, face: Face):
        self._highlightedFace = face
        self.update()

    def highlightedFace(self) -> Face:
        return self._highlightedFace

    def setShowingFaces(self, showing: bool):
        self._isShowingFaces = showing
        self.update()

    def isShowingFaces(self) -> bool:
        return self._isShowingFaces

    def paintEvent(self, event: QtCore.QEvent):
        super().paintEvent(event)

        if not self._isShowingFaces:
            return

        painter = QtGui.QPainter(self)
        painter.setTransform(self._imageToWidgetTransform)  # Rects are in image coordinate space
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for face in self._faces:
            aabb = face.aabb
            painter.setPen(self._getPenForFace(face))
            painter.drawRect(QtCore.QRectF(aabb.x, aabb.y, aabb.width, aabb.height))

    def _getPenForFace(self, face: Face) -> QtGui.QPen:
        if face == self._selectedFace:
            return self._selectedFacePen
        elif face == self._highlightedFace:
            return self._highlightedFacePen
        else:
            return self._defaultFacePen


class ImagePreview(QtWidgets.QWidget):
    """
    A widget that displays an Image with buttons with actions.
    """

    _image: Image = None

    _facesRectsAreVisible: bool = True

    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.setSpacing(0)
        layout.addLayout(buttonsLayout)

        self._openButton = QtWidgets.QPushButton(__("Open"))
        self._openButton.setIcon(QtGui.QIcon("res/img/photo_viewer.png"))
        self._openButton.clicked.connect(self._openButtonClicked)
        buttonsLayout.addWidget(self._openButton)

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
        layout.addWidget(previewFrame)

        self.setLayout(layout)

    def setImage(self, image: Image):
        self._image = image
        if image is not None:
            self._openButton.setEnabled(True)
            self._pixmapDisplay.setPixmap(image.get_pixmap())
            self._pixmapDisplay.setFaces(image.faces)
            self._toggleShowFacesButton.setEnabled(len(image.faces) > 0)
        else:
            self._openButton.setEnabled(False)
            self._pixmapDisplay.setPixmap(None)
            self._pixmapDisplay.setFaces([])
            self._toggleShowFacesButton.setEnabled(False)
        self._refreshFacesButton()

    def image(self) -> Image:
        return self._image

    def _refreshFacesButton(self):
        facesCount = len(self._image.faces) if self._image is not None else 0
        facesButtonText = ""
        if facesCount == 0:
            facesButtonText = __("No faces found")
        else:
            facesButtonText = __("Hide Faces") if self._facesRectsAreVisible else __("Show Faces")
        self._toggleShowFacesButton.setText(facesButtonText)

    @QtCore.Slot()
    def _openButtonClicked(self):
        """
        Called when the user clicks the "Open" button.
        """
        if self._image is not None:
            Application.projectManager().openImageExternally(self._image)

    @QtCore.Slot()
    def _toggleShowFacesButtonClicked(self):
        """
        Called when the user clicks the "Show Faces" button.
        """
        self._facesRectsAreVisible = not self._facesRectsAreVisible
        self._pixmapDisplay.setShowingFaces(self._facesRectsAreVisible)
        self._refreshFacesButton()

    def setSelectedFace(self, face: Face):
        self._pixmapDisplay.setSelectedFace(face)
