from PySide6 import QtCore, QtWidgets
from ..Application import Application
from .FacesGrid import FacesGrid
from .GroupDetailsHeader import GroupDetailsHeaderWidget
from .GroupSelector import GroupSelector
from .GroupsGrid import GroupsGrid
from ..Models import Group, Face, Image
from ..QtHelpers import setSplitterStyle


class GroupFacesWindow(QtWidgets.QWidget):
    """
    A window that allows the user to group faces.
    """

    def __init__(self) -> None:
        """
        Initialize a new instance of the GroupFacesWindow class.
        """
        super().__init__()

        self._workspace = Application.workspace()
        self._workspace.imageAdded.connect(self._onImageAdded)
        self._workspace.imageRemoved.connect(self._onImageRemoved)

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

        # Initialize the groups
        self._groupImagesIfRequired()

    def _refreshGroups(self) -> None:
        groups = self._workspace.project().groups
        self.groupsGrid.setGroups(groups)
        if self._selectedGroup is None and len(self.groupsGrid.groups()) > 0:
            self._onGroupClicked(groups[0])

    def _groupImagesIfRequired(self) -> None:
        """
        Group the images in the current project if required.
        """
        project = self._workspace.project()
        faces_without_groups = project.get_faces_without_group()
        if len(faces_without_groups) == 0:
            self._refreshGroups()
            return  # The faces have already been grouped

        # If the groups are not clustered, then cluster them
        if len(project.groups) == 0:
            project.regroup_faces()
        else:
            # Otherwise, add the faces to the best matching group (or create a new group)
            for face in faces_without_groups:
                project.add_face_to_best_group(face, project.groups[0])

        self._workspace.setDirty()  # The project has changed
        self._refreshGroups()

    @QtCore.Slot(Image)
    def _onImageAdded(self, image: Image) -> None:
        """
        Called when an image is added to the project.
        """
        if len(image.faces) == 0:
            return

        # We will try to find a group for the new image (or a new group if no group is found)
        project = self._workspace.project()
        for face in image.faces:
            project.add_face_to_best_group(face)
        self._workspace.setDirty()
        self._refreshGroups()

    def _onImageRemoved(self, image: Image) -> None:
        """
        Called when an image is removed from the project.
        """
        project = self._workspace.project()
        for face in image.faces:
            project.remove_face_from_groups(face)
        self._workspace.setDirty()
        self._refreshGroups()

    @QtCore.Slot(Face)
    def _onMoveToGroupTriggered(self, face: Face) -> None:
        """
        Called when the user wants to move a face to another group.

        Args:
            face (Face): The face to move.
        """
        if len(face.group.faces) == 1:
            QtWidgets.QMessageBox.warning(self, "Cannot Move Face", "You cannot move the last face in a group.")
            return

        project = self._workspace.project()
        groupsToShow = [group for group in project.groups if group != self._selectedGroup]
        group = GroupSelector.getGroup(groupsToShow, self, "Select a group to move the face to", showNewGroupOption=True)

        if len(group.faces) == 0:  # The user wants to create a new group
            name, ok = QtWidgets.QInputDialog.getText(self, "Group Name", "Enter a name for the new group:")
            if not ok:
                return
            group.name = name.strip()
            project.add_group(group)

        if group:
            self._selectedGroup.remove_face(face)
            group.add_face(face)
            self.detailsGrid.refresh()
            self._refreshGroups()

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
            self._refreshGroups()
            self.detailsHeader.refresh()
            self._workspace.setDirty()

    @QtCore.Slot(Face)
    def _onRemoveFromGroupTriggered(self, face: Face) -> None:
        """
        Called when the user wants to remove a face from a group.

        Args:
            face (Face): The face to remove.
        """
        if len(self._selectedGroup.faces) == 1:
            QtWidgets.QMessageBox.warning(self, "Cannot Remove Face", "You cannot remove the last face from a group.")
            return
        newGroup = Group()
        self._selectedGroup.remove_face(face)
        newGroup.add_face(face)
        newGroup.recompute_centroid()
        self._workspace.project().add_group(newGroup)
        self.detailsGrid.refresh()
        self._refreshGroups()

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
        self.groupsGrid.selectGroup(group)

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
        self._refreshGroups()
        self._workspace.setDirty()

    @QtCore.Slot(Group)
    def _onCombineGroupTriggered(self, groupToCombine: Group) -> None:
        """
        Called when the user wants to combine a group with another group.

        Args:
            groupToCombine (Group): The group to combine.
        """
        project = self._workspace.project()
        groupsToShow = [group for group in project.groups if group != groupToCombine]
        groupToCombineWith = GroupSelector.getGroup(
            groupsToShow, self, "Select a group to combine with")

        if groupToCombineWith:
            groupToCombineWith.merge(groupToCombine)
            project.remove_group(groupToCombine)
            if self._selectedGroup == groupToCombine:
                self._onGroupClicked(groupToCombineWith)
            self._refreshGroups()
            self._workspace.setDirty()
