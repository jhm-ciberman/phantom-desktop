from PySide6 import QtCore, QtGui, QtWidgets

from ..Application import Application
from ..l10n import __
from ..Models import Face
from ..Widgets.GridBase import GridBase


class GroupDetailsGrid(GridBase):
    """
    Widget that displays a list of faces in form of a grid of thumbnails.
    """

    selectedFacesChanged = QtCore.Signal(list)  # list[Face]
    """Emited when a face is clicked."""

    moveToGroupTriggered = QtCore.Signal(list)  # list[Face]
    """Emited when the "Move to group" action is triggered."""

    removeFromGroupTriggered = QtCore.Signal(list)  # list[Face]
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

        self._moveToGroupAction = QtGui.QAction(__("Move to group..."), self)
        self._moveToGroupAction.triggered.connect(self._onMoveToGroupActionTriggered)

        self._removeFromGroupAction = QtGui.QAction(__("Remove from group"), self)
        self._removeFromGroupAction.triggered.connect(self._onRemoveFromGroupActionTriggered)

        self._useAsMainFaceAction = QtGui.QAction(__("Use as main face"), self)
        self._useAsMainFaceAction.triggered.connect(self._onUseAsMainFaceActionTriggered)

        self._exportImagesAction = QtGui.QAction(QtGui.QIcon("res/img/image_save.png"), __("Export Image"), self)
        self._exportImagesAction.triggered.connect(self._onExportImagesActionTriggered)

        self._contextMenu = QtWidgets.QMenu(self)
        self._contextMenu.addAction(self._removeFromGroupAction)
        self._contextMenu.addAction(self._moveToGroupAction)
        self._contextMenu.addAction(self._useAsMainFaceAction)
        self._contextMenu.addSeparator()
        self._contextMenu.addAction(self._exportImagesAction)

        self.setSelectionMode(QtWidgets.QListView.SelectionMode.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self._onSelectionChanged)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Called when the context menu event is triggered.

        Args:
            event (QContextMenuEvent): The event.
        """
        count = len(self.selectedIndexes())
        self._moveToGroupAction.setEnabled(count > 0)
        self._removeFromGroupAction.setEnabled(count > 0)
        self._useAsMainFaceAction.setEnabled(count == 1)
        self._exportImagesAction.setEnabled(count > 0)
        self._exportImagesAction.setText(__("Export Image") if count == 1 else __("Export Images"))

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

        # Select the first item
        if len(self._faces) > 0:
            self.setCurrentIndex(self.model().index(0, 0))

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

    def _currentFaces(self) -> list[Face]:
        """
        Get the faces that are currently selected.

        Returns:
            list[Face]: The faces that are currently selected.
        """
        return [self._faces[qModelIndex.row()] for qModelIndex in self.selectedIndexes()]

    @QtCore.Slot()
    def _onMoveToGroupActionTriggered(self) -> None:
        """
        Called when the move to group action is triggered.
        """
        self.moveToGroupTriggered.emit(self._currentFaces())

    @QtCore.Slot()
    def _onRemoveFromGroupActionTriggered(self) -> None:
        """
        Called when the remove from group action is triggered.
        """
        self.removeFromGroupTriggered.emit(self._currentFaces())

    @QtCore.Slot()
    def _onUseAsMainFaceActionTriggered(self) -> None:
        """
        Called when the use as main face action is triggered.
        """
        self.useAsMainFaceTriggered.emit(self._currentFaces()[0])

    @QtCore.Slot()
    def _onSelectionChanged(self) -> None:
        """
        Called when the selection changes.
        """
        self.selectedFacesChanged.emit(self._currentFaces())

    @QtCore.Slot()
    def _onExportImagesActionTriggered(self) -> None:
        """
        Called when the export images action is triggered.
        """
        images = [face.image for face in self._currentFaces()]
        Application.projectManager().exportImages(self, images)
