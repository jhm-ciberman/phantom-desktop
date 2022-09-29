from PySide6 import QtCore, QtGui, QtWidgets
from .Widgets.PixmapDisplay import PixmapDisplay
from .Image import Group, Face, Image
from .QtHelpers import setSplitterStyle
from .Widgets.GridBase import GridBase
from .Services.ClusteringService import cluster


class _GroupsGrid(GridBase):
    """
    Widget that displays a list of groups of faces in form of a grid of thumbnails.
    """

    groupClicked = QtCore.Signal(Group)
    """Emited when a group is clicked."""

    combineGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Combine group with..." action is triggered"""

    renameGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Rename group" action is triggered"""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _GroupsPreview class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._groups = []  # type: list[Group]
        self.itemClicked.connect(self._onItemClicked)
        self.itemDoubleClicked.connect(self._onItemDoubleClicked)

        self._combineGroupAction = QtGui.QAction("Combine group with...", self)
        self._combineGroupAction.triggered.connect(self._onCombineGroupTriggered)

        self._renameGroupAction = QtGui.QAction(QtGui.QIcon("res/edit.png"), "Rename group", self)
        self._renameGroupAction.triggered.connect(self._onRenameGroupTriggered)

        self._contextMenu = QtWidgets.QMenu(self)
        self._contextMenu.addAction(self._combineGroupAction)
        self._contextMenu.addAction(self._renameGroupAction)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Called when the widget receives a context menu event.

        Args:
            event (QContextMenuEvent): The event.
        """
        self._contextMenu.exec_(event.globalPos())

    def setGroups(self, groups: list[Group]) -> None:
        """
        Set the groups to display.

        Args:
            groups (list[Group]): The groups to display.
        """
        self.clear()
        self._groups = groups.copy()
        # Sort groups by number of faces in them, so that the largest groups are at the top
        self._groups.sort(key=lambda g: len(g.faces), reverse=True)

        for group in self._groups:
            if len(group.faces) == 0:
                continue
            w, h = self.iconSize().width(), self.iconSize().height()
            pixmap = group.main_face.get_avatar_pixmap(w, h)
            text = group.name if group.name else ""
            self._addItemCore(pixmap, text)

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

    def removeGroup(self, group: Group) -> None:
        """
        Remove the group from the grid.

        Args:
            group (Group): The group to remove.
        """
        index = self._groups.index(group)
        self.takeItem(index)
        self._groups.remove(group)

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
        self.groupClicked.emit(self._groups[self.row(item)])

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemDoubleClicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """
        Called when an item is double-clicked.

        Args:
            item (QListWidgetItem): The item that was double-clicked.
        """
        self.renameGroupTriggered.emit(self._groups[self.row(item)])

    @QtCore.Slot()
    def _onCombineGroupTriggered(self) -> None:
        """
        Called when the "Combine group with..." action is triggered.
        """
        self.combineGroupTriggered.emit(self._groups[self.currentRow()])

    @QtCore.Slot()
    def _onRenameGroupTriggered(self) -> None:
        """
        Called when the "Rename group" action is triggered.
        """
        self.renameGroupTriggered.emit(self._groups[self.currentRow()])


class _FacesGrid(GridBase):
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

        self._moveToGroupAction = QtGui.QAction("Move to group...", self)
        self._moveToGroupAction.triggered.connect(self._onMoveToGroupActionTriggered)

        self._removeFromGroupAction = QtGui.QAction("Remove from group", self)
        self._removeFromGroupAction.triggered.connect(self._onRemoveFromGroupActionTriggered)

        self._useAsMainFaceAction = QtGui.QAction("Use as main face", self)
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
            imageBasename = face.image.basename
            self._addItemCore(pixmap, imageBasename)

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


class _GroupDetailsHeaderWidget(QtWidgets.QWidget):
    """
    The header for the group details
    """

    renameGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Rename group" action is triggered."""

    combineGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Combine group" action is triggered."""

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
        self._editNameButton.setContentsMargins(40, 0, 0, 0)
        self._editNameButton.clicked.connect(self._onEditNameClicked)
        infoLayoutTop.addWidget(self._editNameButton)

        self._combineGroupButton = QtWidgets.QPushButton("Combine group")
        self._combineGroupButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._combineGroupButton.setContentsMargins(20, 0, 0, 0)
        self._combineGroupButton.clicked.connect(self._onCombineGroupClicked)
        infoLayoutTop.addWidget(self._combineGroupButton)

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

    def refresh(self) -> None:
        """
        Refresh the widget.
        """
        self.setGroup(self._group)

    @QtCore.Slot()
    def _onEditNameClicked(self) -> None:
        """
        Called when the edit name button is clicked.
        """
        self.renameGroupTriggered.emit(self._group)

    @QtCore.Slot()
    def _onCombineGroupClicked(self) -> None:
        """
        Called when the combine group button is clicked.
        """
        self.combineGroupTriggered.emit(self._group)


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


class _GroupSelector(QtWidgets.QDialog):
    """
    A widget that contains a list of groups and a search box. The groups are displayed
    with their main face.
    """

    def __init__(self, groups: list[Group], parent: QtWidgets.QWidget = None, title: str = None) -> None:
        """
        Initialize a new instance of the _GroupSelector class.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Select a group" if title is None else title)
        self.setModal(True)
        self.resize(400, 400)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._searchBox = QtWidgets.QLineEdit()
        self._searchBox.setPlaceholderText("Search")
        self._searchBox.textChanged.connect(self._onSearchTextChanged)
        self._searchBox.setClearButtonEnabled(True)
        layout.addWidget(self._searchBox)

        self._groupsGrid = _GroupSelectorGrid()
        self._groupsGrid.itemSelected.connect(self._onGroupSelected)
        layout.addWidget(self._groupsGrid)

        selectCancelLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(selectCancelLayout)

        selectCancelLayout.addStretch()

        self._selectButton = QtWidgets.QPushButton("Select")
        self._selectButton.setEnabled(False)
        self._selectButton.clicked.connect(self._onSelectClicked)

        self._cancelButton = QtWidgets.QPushButton("Cancel")
        self._cancelButton.clicked.connect(self._onCancelClicked)

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

    @QtCore.Slot()
    def _onSelectClicked(self) -> None:
        """
        Called when the select button is clicked.
        """
        self.accept()

    @QtCore.Slot()
    def _onCancelClicked(self) -> None:
        """
        Called when the cancel button is clicked.
        """
        self.reject()

    def selectedGroup(self) -> Group:
        """
        Get the selected group.

        Returns:
            Group: The selected group.
        """
        return self._groupsGrid.selectedItem().data(QtCore.Qt.UserRole)  # type: Group

    @staticmethod
    def getGroup(groups: list[Group], parent: QtWidgets.QWidget = None, title: str = None) -> Group:
        """
        Get a group from the user.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.

        Returns:
            Group: The selected group.
        """
        dialog = _GroupSelector(groups, parent, title)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            return dialog.selectedGroup()
        return None


class GroupFacesWindow(QtWidgets.QWidget):
    """
    A window that allows the user to group faces.
    """

    def __init__(self, images: list[Image]) -> None:
        """
        Initialize a new instance of the GroupFacesWindow class.
        """
        super().__init__()

        self._images = images
        self._groups = self._groupImages(images)  # type: list[Group]
        self._selectedGroup = None  # type: Group

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

        self.groupsGrid = _GroupsGrid()
        splitter.addWidget(self.groupsGrid)

        detailsWidget = QtWidgets.QWidget()
        detailsLayout = QtWidgets.QVBoxLayout()
        detailsLayout.setContentsMargins(0, 0, 0, 0)
        detailsWidget.setLayout(detailsLayout)

        self.detailsHeader = _GroupDetailsHeaderWidget()
        self.detailsGrid = _FacesGrid()

        detailsLayout.addWidget(self.detailsHeader)
        detailsLayout.addWidget(self.detailsGrid)

        splitter.addWidget(detailsWidget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # Connect signals
        self.groupsGrid.groupClicked.connect(self._onGroupClicked)
        self.groupsGrid.renameGroupTriggered.connect(self._onRenameGroupTriggered)
        self.groupsGrid.combineGroupTriggered.connect(self._onCombineGroupTriggered)
        self.detailsGrid.faceClicked.connect(self._onFaceClicked)
        self.detailsGrid.moveToGroupTriggered.connect(self._onMoveToGroupTriggered)
        self.detailsGrid.removeFromGroupTriggered.connect(self._onRemoveFromGroupTriggered)
        self.detailsGrid.useAsMainFaceTriggered.connect(self._onUseAsMainFaceTriggered)
        self.detailsHeader.renameGroupTriggered.connect(self._onRenameGroupTriggered)
        self.detailsHeader.combineGroupTriggered.connect(self._onCombineGroupTriggered)

        self.groupsGrid.setGroups(self._groups)
        if len(self._groups) > 0:
            self._onGroupClicked(self._groups[0])

    def _groupImages(self, images: list[Image]) -> list[Group]:
        """
        Group the images.

        Args:
            images (list[Image]): The images to group.

        Returns:
            list[Group]: The groups.
        """
        faces = []
        for image in images:
            faces.extend(image.faces)
        return cluster(faces)

    @QtCore.Slot(Face)
    def _onMoveToGroupTriggered(self, face: Face) -> None:
        """
        Called when the user wants to move a face to another group.

        Args:
            face (Face): The face to move.
        """
        groupsToShow = [group for group in self._groups if group != self._selectedGroup]
        group = _GroupSelector.getGroup(groupsToShow, self, "Select a group to move the face to")
        if group:
            self._selectedGroup.remove_face(face)
            group.add_face(face)
            self.detailsGrid.refresh()
            self.groupsGrid.updateGroup(self._selectedGroup)
            self.groupsGrid.updateGroup(group)

    @QtCore.Slot(Group)
    def _onRenameGroupTriggered(self, group: Group) -> None:
        """
        Called when the user wants to rename a group.

        Args:
            group (Group): The group to rename.
        """
        name, ok = QtWidgets.QInputDialog.getText(self, "Group Name", "Enter a name for the group:", text=group.name)
        if ok:
            group.name = name
            self.groupsGrid.updateGroup(group)
            self.detailsHeader.refresh()

    @QtCore.Slot(Face)
    def _onRemoveFromGroupTriggered(self, face: Face) -> None:
        """
        Called when the user wants to remove a face from a group.

        Args:
            face (Face): The face to remove.
        """
        self._selectedGroup.remove_face(face)
        self.detailsGrid.refresh()
        self.groupsGrid.updateGroup(self._selectedGroup)

    @QtCore.Slot(Group)
    def _onGroupClicked(self, group: Group) -> None:
        """
        Called when the user clicks a group.

        Args:
            group (Group): The group.
        """
        self._selectedGroup = group
        self.detailsGrid.setFaces(group.faces)
        self.detailsHeader.setGroup(group)

    @QtCore.Slot(Face)
    def _onFaceClicked(self, face: Face) -> None:
        """
        Called when the user clicks a face.

        Args:
            face (Face): The face.
        """
        pass

    @QtCore.Slot(Face)
    def _onUseAsMainFaceTriggered(self, face: Face) -> None:
        """
        Called when the user wants to use a face as the main face.

        Args:
            face (Face): The face.
        """
        self._selectedGroup.main_face_override = face
        self.detailsGrid.refresh()
        self.groupsGrid.updateGroup(self._selectedGroup)

    @QtCore.Slot(Group)
    def _onCombineGroupTriggered(self, groupToCombine: Group) -> None:
        """
        Called when the user wants to combine a group with another group.

        Args:
            groupToCombine (Group): The group to combine.
        """
        groupsToShow = [group for group in self._groups if group != groupToCombine]
        groupToCombineWith = _GroupSelector.getGroup(groupsToShow, self, "Select a group to combine with")

        if groupToCombineWith:
            groupToCombineWith.merge(groupToCombine)

            self._groups.remove(groupToCombine)
            self.groupsGrid.removeGroup(groupToCombine)
            self.detailsGrid.refresh()
            self.groupsGrid.updateGroup(groupToCombineWith)
