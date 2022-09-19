from PySide6 import QtCore, QtGui, QtWidgets
from .Image import Image, Face
from .Services.ClusteringService import Group, cluster
from .QtHelpers import setSplitterStyle
from .Widgets.GridBase import GridBase


class _GroupsGrid(GridBase):
    """
    Widget that displays a list of groups of faces in form of a grid of thumbnails.
    """

    groupClicked = QtCore.Signal(Group)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _GroupsPreview class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._groups = []  # type: list[Group]
        self.itemClicked.connect(self._onItemClicked)

    def setGroups(self, groups: list[Group]) -> None:
        """
        Set the groups to display.

        Args:
            groups (list[Group]): The groups to display.
        """
        self.clear()
        self._groups = groups
        # Sort groups by number of faces in them, so that the largest groups are at the top
        self._groups.sort(key=lambda g: len(g.faces), reverse=True)

        for group in self._groups:
            if len(group.faces) == 0:
                continue
            w, h = self.iconSize().width(), self.iconSize().height()
            pixmap = group.main_face.get_pixmap(w, h)
            text = group.name if group.name else "(No name)"
            self._addItemCore(pixmap, text)

    def groups(self) -> list[Group]:
        """
        Get the groups that are displayed.

        Returns:
            list[Group]: The groups that are displayed.
        """
        return self._groups

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemClicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """
        Called when an item is clicked.

        Args:
            item (QListWidgetItem): The item that was clicked.
        """
        group = self._groups[self.row(item)]
        self.groupClicked.emit(group)


class _FacesGrid(GridBase):
    """
    Widget that displays a list of faces in form of a grid of thumbnails.
    """

    onFaceClicked = QtCore.Signal(Face)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _FacesGrid class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._faces = []  # type: list[Face]
        self.itemClicked.connect(self._onItemClicked)

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
            imageBasename = face.image.basename
            self._addItemCore(pixmap, imageBasename)

    def faces(self) -> list[Face]:
        """
        Get the faces that are displayed.

        Returns:
            list[Face]: The faces that are displayed.
        """
        return self._faces

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemClicked(self, item: QtWidgets.QWidgetItem) -> None:
        """
        Called when an item is clicked.

        Args:
            item (QListWidgetItem): The item that was clicked.
        """
        face = self._faces[self.row(item)]
        self.onFaceClicked.emit(face)


class GroupFacesWindow(QtWidgets.QWidget):
    def __init__(self, images: list[Image]) -> None:
        super().__init__()

        self._images = images

        self.setMinimumSize(800, 600)
        self.setWindowTitle("Group Faces - Phantom")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        splitter.setContentsMargins(10, 10, 10, 10)
        setSplitterStyle(splitter)
        layout.addWidget(splitter)

        self._groupsGrid = _GroupsGrid()
        self._groupsGrid.groupClicked.connect(self._onGroupClicked)
        splitter.addWidget(self._groupsGrid)

        # Collect all faces from all images
        faces = []
        for image in self._images:
            faces.extend(image.faces)
        groups = cluster(faces)

        self._groupsGrid.setGroups(groups)

        self._facesGrid = _FacesGrid()
        splitter.addWidget(self._facesGrid)

        self._selectedGroup = None  # type: Group

    @QtCore.Slot(Group)
    def _onGroupClicked(self, group: Group) -> None:
        """
        Called when a group is clicked.

        Args:
            group (Group): The group that was clicked.
        """
        self._selectedGroup = group
        self._facesGrid.setFaces(group.faces)