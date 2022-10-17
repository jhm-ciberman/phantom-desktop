from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __
from ..Models import Face
from ..Widgets.GridBase import GridBase


class FacesGrid(GridBase):
    """
    Widget that displays a list of faces in form of a grid of thumbnails.
    """

    faceClicked = QtCore.Signal(Face)
    """Emited when a face is clicked."""

    moveToGroupTriggered = QtCore.Signal(Face)
    """Emited when the "Move to group" action is triggered."""

    removeFromGroupTriggered = QtCore.Signal(Face)
    """Emited when the "Remove from group" action is triggered."""

    useAsMainFaceTriggered = QtCore.Signal(Face)
    """Emited when the "Use as main face" action is triggered."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _FacesGrid class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._faces = []  # type: list[Face]
        self.itemClicked.connect(self._onItemClicked)

        self._moveToGroupAction = QtGui.QAction(__("Move to group..."), self)
        self._moveToGroupAction.triggered.connect(self._onMoveToGroupActionTriggered)

        self._removeFromGroupAction = QtGui.QAction(__("Remove from group"), self)
        self._removeFromGroupAction.triggered.connect(self._onRemoveFromGroupActionTriggered)

        self._useAsMainFaceAction = QtGui.QAction(__("Use as main face"), self)
        self._useAsMainFaceAction.triggered.connect(self._onUseAsMainFaceActionTriggered)

        self._contextMenu = QtWidgets.QMenu(self)
        self._contextMenu.addAction(self._removeFromGroupAction)
        self._contextMenu.addAction(self._moveToGroupAction)
        self._contextMenu.addAction(self._useAsMainFaceAction)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Called when the context menu event is triggered.

        Args:
            event (QContextMenuEvent): The event.
        """
        item = self.itemAt(event.pos())
        if item is None:
            return
        self._contextMenu.exec_(event.globalPos())

    def setFaces(self, faces: list[Face]) -> None:
        """
        Set the faces to display.

        Args:
            faces (list[Face]): The faces to display.
        """
        self.clear()
        self._faces = faces

        # sort by confidence
        self._faces.sort(key=lambda f: f.confidence, reverse=True)

        for face in self._faces:
            pixmap = face.image.get_pixmap()
            imageBasename = face.image.display_name
            self.addItemCore(pixmap, imageBasename)

    def refresh(self) -> None:
        """
        Refresh the grid.
        """
        self.setFaces(self._faces)

    def faces(self) -> list[Face]:
        """
        Get the faces that are displayed.

        Returns:
            list[Face]: The faces that are displayed.
        """
        return self._faces

    def _currentFace(self) -> Face:
        """
        Get the currently selected face.

        Returns:
            Face: The currently selected face.
        """
        item = self.currentItem()
        if item is None:
            return None
        return self._faces[self.row(item)]

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemClicked(self, item: QtWidgets.QWidgetItem) -> None:
        """
        Called when an item is clicked.

        Args:
            item (QListWidgetItem): The item that was clicked.
        """
        self.faceClicked.emit(self._currentFace())

    @QtCore.Slot()
    def _onMoveToGroupActionTriggered(self) -> None:
        """
        Called when the move to group action is triggered.
        """
        self.moveToGroupTriggered.emit(self._currentFace())

    @QtCore.Slot()
    def _onRemoveFromGroupActionTriggered(self) -> None:
        """
        Called when the remove from group action is triggered.
        """
        self.removeFromGroupTriggered.emit(self._currentFace())

    @QtCore.Slot()
    def _onUseAsMainFaceActionTriggered(self) -> None:
        """
        Called when the use as main face action is triggered.
        """
        self.useAsMainFaceTriggered.emit(self._currentFace())
