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
    """Emited when a group is clicked."""

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

    def updateGroup(self, group: Group) -> None:
        """
        Update the group in the grid.

        Args:
            group (Group): The group to update.
        """
        index = self._groups.index(group)
        item = self.item(index)
        if item is None:
            return
        w, h = self.iconSize().width(), self.iconSize().height()
        pixmap = group.main_face.get_avatar_pixmap(w, h)
        text = group.name if group.name else ""
        self._setItemCore(item, pixmap, text)


class _FacesGrid(GridBase):
    """
    Widget that displays a list of faces in form of a grid of thumbnails.
    """

    faceClicked = QtCore.Signal(Face)

    moveToGroupTriggered = QtCore.Signal(Face)

    removeFromGroupTriggered = QtCore.Signal(Face)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _FacesGrid class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._faces = []  # type: list[Face]
        self.itemClicked.connect(self._onItemClicked)

        self._moveToGroupAction = QtGui.QAction("Move to group...", self)
        self._moveToGroupAction.triggered.connect(self._onMoveToGroupActionTriggered)

        self._removeFromGroupAction = QtGui.QAction("Remove from group", self)
        self._removeFromGroupAction.triggered.connect(self._onRemoveFromGroupActionTriggered)

        self._contextMenu = QtWidgets.QMenu(self)
        self._contextMenu.addAction(self._removeFromGroupAction)
        self._contextMenu.addAction(self._moveToGroupAction)

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
        self.faceClicked.emit(face)

    @QtCore.Slot()
    def _onMoveToGroupActionTriggered(self) -> None:
        """
        Called when the move to group action is triggered.
        """
        item = self.currentItem()
        if item is None:
            return
        face = self._faces[self.row(item)]
        self.moveToGroupTriggered.emit(face)

    @QtCore.Slot()
    def _onRemoveFromGroupActionTriggered(self) -> None:
        """
        Called when the remove from group action is triggered.
        """
        item = self.currentItem()
        if item is None:
            return
        face = self._faces[self.row(item)]
        self.removeFromGroupTriggered.emit(face)


class _GroupDetailsHeaderWidget(QtWidgets.QWidget):
    """
    The header for the group details
    """

    groupRenamed = QtCore.Signal(Group)
    """Emited when the group is renamed."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the GroupDetailsHeaderWidget class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._group = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setFixedHeight(84)  # 64 + 10 + 10

        headerLayout = QtWidgets.QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(headerLayout)

        self._mainFaceIcon = PixmapDisplay()
        self._mainFaceIcon.setFixedSize(64, 64)
        headerLayout.addWidget(self._mainFaceIcon)

        infoLayout = QtWidgets.QVBoxLayout()
        infoLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        infoLayout.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        infoLayout.setContentsMargins(10, 0, 0, 0)
        headerLayout.addLayout(infoLayout)

        infoLayoutTop = QtWidgets.QHBoxLayout()
        infoLayout.addLayout(infoLayoutTop)

        self._nameLabel = QtWidgets.QLabel()
        self._nameLabel.setFont(QtGui.QFont("Arial", 20))
        self._nameLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self._nameLabel.setText("")
        infoLayoutTop.addWidget(self._nameLabel)

        self._editNameButton = QtWidgets.QPushButton(QtGui.QIcon("res/edit.png"), "Edit name")
        self._editNameButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._editNameButton.setContentsMargins(20, 0, 0, 0)
        self._editNameButton.clicked.connect(self._onEditNameClicked)
        infoLayoutTop.addWidget(self._editNameButton)

        self._subtitleLabel = QtWidgets.QLabel()
        self._subtitleLabel.setFont(QtGui.QFont("Arial", 12))
        self._editNameButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._subtitleLabel.setText("")
        self._subtitleLabel.setStyleSheet("color: gray;")
        infoLayout.addWidget(self._subtitleLabel)

    def setGroup(self, group: Group) -> None:
        """
        Set the group to display.

        Args:
            group (Group): The group to display.
        """
        self._group = group

        w, h = self._mainFaceIcon.size().width(), self._mainFaceIcon.size().height()
        self._mainFaceIcon.setPixmap(group.main_face.get_avatar_pixmap(w, h))
        name = group.name if group.name else "Add a name to this person"
        self._nameLabel.setText(name)
        uniqueImagesCount = group.count_unique_images()
        self._subtitleLabel.setText(f"{uniqueImagesCount} photos" if uniqueImagesCount > 1 else "1 photo")
        titleColor = "black" if group.name else "#0078d7"
        self._nameLabel.setStyleSheet(f"color: {titleColor};")

    @QtCore.Slot()
    def _onEditNameClicked(self) -> None:
        """
        Called when the edit name button is clicked.
        """
        name, ok = QtWidgets.QInputDialog.getText(self, "Edit name", "Enter a new name:", text=self._group.name)
        if ok:
            self._group.name = name
            self.groupRenamed.emit(self._group)
            self.setGroup(self._group)


class _GroupSelectorGrid(GridBase):
    """The grid that contains the groups."""

    def addGroup(self, group: Group) -> None:
        """
        Add a group to the grid.

        Args:
            group (Group): The group to add.
        """
        gridSize = self.gridSize()
        pixmap = group.main_face.get_avatar_pixmap(gridSize.width(), gridSize.height())
        text = group.name if group.name else ""
        self._addItemCore(pixmap, text, group)


class _GroupSelector(QtWidgets.QWidget):
    """
    A widget that contains a list of groups and a search box. The groups are displayed
    with their main face.
    """

    groupSelected = QtCore.Signal(Group)
    """Emited when a group is selected."""

    def __init__(self, groups: list[Group], parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _GroupSelector class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._searchBox = QtWidgets.QLineEdit()
        self._searchBox.setPlaceholderText("Search")
        self._searchBox.textChanged.connect(self._onSearchTextChanged)
        self._searchBox.setClearButtonEnabled(True)
        layout.addWidget(self._searchBox)

        self._groupsGrid = _GroupSelectorGrid()
        self._groupsGrid.itemClicked.connect(self._onGroupSelected)
        layout.addWidget(self._groupsGrid)

        for group in groups:
            self._groupsGrid.addGroup(group)

    def _onSearchTextChanged(self, text: str) -> None:
        """
        Called when the search text changes.

        Args:
            text (str): The new text.
        """
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            group = item.data(QtCore.Qt.UserRole)  # type: Group
            name = group.name.lower() if group.name else ""
            item.setHidden(text.lower() not in name)

    def _onGroupSelected(self) -> None:
        """
        Called when a group is selected.
        """
        item = self._groupsGrid.currentItem()
        group = item.data(QtCore.Qt.UserRole)  # type: Group
        self.groupSelected.emit(group)

    @staticmethod
    def selectGroup(groups: list[Group], parent: QtWidgets.QWidget) -> Group:
        """
        Show the group selector as a modal dialog.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.

        Returns:
            Group: The selected group.
        """
        dialog = QtWidgets.QDialog(parent)
        dialog.setWindowTitle("Select a group")
        dialog.setModal(True)
        dialog.resize(400, 400)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        dialog.setLayout(layout)

        groupSelector = _GroupSelector(groups)
        groupSelector.groupSelected.connect(dialog.accept)
        layout.addWidget(groupSelector)

        dialog.exec()
        return groupSelector._groupsGrid.currentItem().data(QtCore.Qt.UserRole)


class GroupDetailsWidget(QtWidgets.QWidget):
    """
    A widget that contains a top header with available actions and a grid with all the
    faces that belongs to a group
    """

    faceClicked = QtCore.Signal(Face)
    """Emited when a face is clicked."""

    groupRenamed = QtCore.Signal(Group)
    """Emited when the group is renamed."""

    moveFaceToGroupTriggered = QtCore.Signal(Face)
    """Emited when the user wants to move a face to another group."""

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

        self._header = _GroupDetailsHeaderWidget()
        self._header.groupRenamed.connect(self.groupRenamed)

        self._facesGrid = _FacesGrid()
        self._facesGrid.faceClicked.connect(self._onFaceClicked)
        self._facesGrid.moveToGroupTriggered.connect(self.moveFaceToGroupTriggered)

        layout.addWidget(self._header)
        layout.addWidget(self._facesGrid)

    def setGroup(self, group: Group) -> None:
        """
        Set the group to display.

        Args:
            group (Group): The group to display.
        """
        self._group = group
        self._header.setGroup(group)
        self._facesGrid.setFaces(group.faces)

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
        self._groupDetails.groupRenamed.connect(self._onGroupRenamed)
        self._groupDetails.moveFaceToGroupTriggered.connect(self._onMoveFaceToGroupTriggered)
        splitter.addWidget(self._groupDetails)

        if len(groups) > 0:
            self._groupDetails.setGroup(groups[0])

        self._faceToMove = None  # type: Face

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

    @QtCore.Slot(Group)
    def _onGroupRenamed(self, group: Group) -> None:
        """
        Called when a group is renamed.

        Args:
            group (Group): The group that was renamed.
        """
        self._groupsGrid.updateGroup(group)

    @QtCore.Slot(Face)
    def _onMoveFaceToGroupTriggered(self, face: Face) -> None:
        """
        Called when the user wants to move a face to another group.

        Args:
            face (Face): The face to move.
        """
        oldGroup = self._groupDetails.group()
        groups = self._groupsGrid.groups().copy()
        groups.remove(oldGroup)
        group = _GroupSelector.selectGroup(groups, self)
        if group:
            group.add_face(face)
            oldGroup.remove_face(face)
            self._groupsGrid.updateGroup(group)
            self._groupsGrid.updateGroup(oldGroup)
            self._groupDetails.setGroup(oldGroup)
