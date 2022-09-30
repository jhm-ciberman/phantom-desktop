from PySide6 import QtCore, QtWidgets
from .FacesGrid import FacesGrid
from .GroupDetailsHeader import GroupDetailsHeaderWidget
from .GroupSelector import GroupSelector
from .GroupsGrid import GroupsGrid
from ..Image import Group, Face, Image
from ..QtHelpers import setSplitterStyle
from .ClusteringService import cluster


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

        self.groupsGrid = GroupsGrid()
        splitter.addWidget(self.groupsGrid)

        detailsWidget = QtWidgets.QWidget()
        detailsLayout = QtWidgets.QVBoxLayout()
        detailsLayout.setContentsMargins(0, 0, 0, 0)
        detailsWidget.setLayout(detailsLayout)

        self.detailsHeader = GroupDetailsHeaderWidget()
        self.detailsGrid = FacesGrid()

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
        group = GroupSelector.getGroup(groupsToShow, self, "Select a group to move the face to")
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
        groupToCombineWith = GroupSelector.getGroup(groupsToShow, self, "Select a group to combine with")

        if groupToCombineWith:
            groupToCombineWith.merge(groupToCombine)

            self._groups.remove(groupToCombine)
            self.groupsGrid.removeGroup(groupToCombine)
            self.detailsGrid.refresh()
            self.groupsGrid.updateGroup(groupToCombineWith)
