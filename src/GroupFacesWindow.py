from PySide6 import QtCore, QtGui, QtWidgets
from .Widgets.PixmapDisplay import PixmapDisplay
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

        self.resize(self.gridSize().width() * 3, self.height())

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
            pixmap = group.main_face.get_avatar_pixmap(w, h)
            text = group.name if group.name else ""
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


class GroupDetailsWidget(QtWidgets.QWidget):
    """
    A widget that contains a top header with available actions and a grid with all the
    faces that belongs to a group
    """

    faceClicked = QtCore.Signal(Face)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the GroupDetailsWidget class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._group = None  # type: Group

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._header = QtWidgets.QWidget()
        self._header.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        self._header.setFixedHeight(160)

        headerLayout = QtWidgets.QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        self._header.setLayout(headerLayout)

        self._mainFaceIcon = PixmapDisplay()
        self._mainFaceIcon.setFixedSize(150, 150)
        headerLayout.addWidget(self._mainFaceIcon)

        infoLayout = QtWidgets.QVBoxLayout()
        infoLayout.setContentsMargins(10, 0, 0, 0)
        headerLayout.addLayout(infoLayout)

        infoLayoutTop = QtWidgets.QHBoxLayout()
        infoLayout.addLayout(infoLayoutTop)

        self._nameLabel = QtWidgets.QLabel()
        self._nameLabel.setFont(QtGui.QFont("Arial", 20))
        self._nameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self._nameLabel.setText("")
        infoLayoutTop.addWidget(self._nameLabel)

        self.setStyleSheet("QPushButton { padding: 10px 5px; }")
        self._editNameButton = QtWidgets.QPushButton(QtGui.QIcon("res/edit.png"), "Edit name")
        self._editNameButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self._editNameButton.setContentsMargins(10, 0, 0, 0)
        self._editNameButton.clicked.connect(self._onEditNameClicked)
        infoLayoutTop.addWidget(self._editNameButton)

        self._subtitleLabel = QtWidgets.QLabel()
        self._subtitleLabel.setFont(QtGui.QFont("Arial", 12))
        self._subtitleLabel.setText("")
        self._subtitleLabel.setStyleSheet("color: gray;")
        infoLayout.addWidget(self._subtitleLabel)

        self._facesGrid = _FacesGrid()
        self._facesGrid.onFaceClicked.connect(self._onFaceClicked)

        layout.addWidget(self._header)
        layout.addWidget(self._facesGrid)

    def setGroup(self, group: Group) -> None:
        """
        Set the group to display.

        Args:
            group (Group): The group to display.
        """
        self._group = group
        self._mainFaceIcon.setPixmap(group.main_face.get_avatar_pixmap(150, 150))
        name = group.name if group.name else "(No name)"
        self._nameLabel.setText(name)
        self._facesGrid.setFaces(group.faces)
        unique_images_count = group.count_unique_images()
        self._subtitleLabel.setText(f"{unique_images_count} photos")

    def group(self) -> Group:
        """
        Get the group that is displayed.

        Returns:
            Group: The group that is displayed.
        """
        return self._group

    @QtCore.Slot(Face)
    def _onFaceClicked(self, face: Face) -> None:
        """
        Called when a face is clicked.

        Args:
            face (Face): The face that was clicked.
        """
        self.faceClicked.emit(face)

    @QtCore.Slot()
    def _onEditNameClicked(self) -> None:
        """
        Called when the edit name button is clicked.
        """
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Edit group name", "Enter a name for the group:")
        if ok:
            self._group.name = name
            self._nameLabel.setText(name)


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

        self._groupDetails = GroupDetailsWidget()
        self._groupDetails.faceClicked.connect(self._onFaceClicked)
        splitter.addWidget(self._groupDetails)

        if len(groups) > 0:
            self._groupDetails.setGroup(groups[0])

    @QtCore.Slot(Group)
    def _onGroupClicked(self, group: Group) -> None:
        """
        Called when a group is clicked.

        Args:
            group (Group): The group that was clicked.
        """
        self._groupDetails.setGroup(group)

    @QtCore.Slot(Face)
    def _onFaceClicked(self, face: Face) -> None:
        """
        Called when a face is clicked.

        Args:
            face (Face): The face that was clicked.
        """
        pass
