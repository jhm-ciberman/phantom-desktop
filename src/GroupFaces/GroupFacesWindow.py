from PySide6 import QtCore, QtWidgets

from ..Main.InspectorPanel import InspectorPanel


from ..Application import Application
from ..l10n import __
from ..Models import Face, Group, Image
from .ClusteringService import MergeOportunity
from .FacesGrid import FacesGrid
from .GroupDetailsHeader import GroupDetailsHeaderWidget
from .GroupSelector import GroupSelector
from .GroupsGrid import GroupsGrid
from .MergingWizard import MergingWizard


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
        self._workspace.imagesAdded.connect(self._onImagesAdded)
        self._workspace.imagesRemoved.connect(self._onImageRemoved)

        self._selectedGroup = None  # type: Group

        self.setMinimumSize(800, 600)
        self.setWindowTitle(__("Group Faces") + " - Phantom")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        splitter.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(splitter)

        leftColumnWidget = QtWidgets.QWidget()
        leftColumnLayout = QtWidgets.QVBoxLayout()
        leftColumnLayout.setContentsMargins(0, 0, 0, 0)
        leftColumnWidget.setLayout(leftColumnLayout)
        splitter.addWidget(leftColumnWidget)

        self._mergingWizard = MergingWizard(self._workspace.project(), leftColumnWidget)
        leftColumnLayout.addWidget(self._mergingWizard)

        self._groupsGrid = GroupsGrid()
        leftColumnLayout.addWidget(self._groupsGrid)

        detailsWidget = QtWidgets.QWidget()
        detailsLayout = QtWidgets.QVBoxLayout()
        detailsLayout.setContentsMargins(0, 0, 0, 0)
        detailsWidget.setLayout(detailsLayout)

        self._detailsHeader = GroupDetailsHeaderWidget()
        self._detailsGrid = FacesGrid()

        detailsLayout.addWidget(self._detailsHeader)
        detailsLayout.addWidget(self._detailsGrid)
        splitter.addWidget(detailsWidget)

        self._inspectorPanel = InspectorPanel()
        splitter.addWidget(self._inspectorPanel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

        # Connect signals
        self._groupsGrid.groupClicked.connect(self._onGroupClicked)
        self._groupsGrid.renameGroupTriggered.connect(self._onRenameGroupTriggered)
        self._groupsGrid.combineGroupTriggered.connect(self._onCombineGroupTriggered)
        self._detailsGrid.faceClicked.connect(self._onFaceClicked)
        self._detailsGrid.moveToGroupTriggered.connect(self._onMoveToGroupTriggered)
        self._detailsGrid.removeFromGroupTriggered.connect(self._onRemoveFromGroupTriggered)
        self._detailsGrid.useAsMainFaceTriggered.connect(self._onUseAsMainFaceTriggered)
        self._detailsHeader.renameGroupTriggered.connect(self._onRenameGroupTriggered)
        self._detailsHeader.combineGroupTriggered.connect(self._onCombineGroupTriggered)
        self._mergingWizard.groupsMerged.connect(self._onGroupsMerged)
        self._mergingWizard.groupsDontMerged.connect(self._onGroupsDontMerged)

        # Initialize the groups
        self._groupImagesIfRequired()

    def _refreshGroups(self) -> None:
        groups = self._workspace.project().groups
        self._groupsGrid.setGroups(groups)
        if self._selectedGroup is None and len(self._groupsGrid.groups()) > 0:
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
        self._mergingWizard.recalculateMergeOpportunities()

    def _collectFaces(self, images: list[Image]) -> list[Face]:
        """
        Collect all the faces from the specified images.
        """
        faces = []
        for image in images:
            faces.extend(image.faces)
        return faces

    @QtCore.Slot(list)
    def _onImagesAdded(self, images: list[Image]) -> None:
        """
        Called when one or more images are added to the project.
        """
        faces = self._collectFaces(images)
        if len(faces) == 0:
            return

        # We will try to find a group for the new image (or a new group if no group is found)
        project = self._workspace.project()
        for face in faces:
            project.add_face_to_best_group(face)
        self._workspace.setDirty()
        self._refreshGroups()

    @QtCore.Slot(list)
    def _onImageRemoved(self, images: list[Image]) -> None:
        """
        Called when one or more images are removed from the project.
        """
        faces = self._collectFaces(images)
        project = self._workspace.project()
        for face in faces:
            project.remove_face_from_groups(face)
        self._workspace.setDirty()
        self._refreshGroups()

    @QtCore.Slot(list)
    def _onMoveToGroupTriggered(self, faces: list[Face]) -> None:
        """
        Called when the user wants to move one or more faces to a group.

        Args:
            faces (list[Face]): The faces to move.
        """
        if len(self._selectedGroup.faces) == len(faces):
            QtWidgets.QMessageBox.warning(self, __("Cannot Move Face"), __("You cannot move the last face in a group."))
            return

        project = self._workspace.project()
        groupsToShow = [group for group in project.groups if group != self._selectedGroup]
        group = GroupSelector.getGroup(groupsToShow, self, __("Select a group to move the face to"), showNewGroupOption=True)

        if group is None:
            return

        if len(group.faces) == 0:  # The user wants to create a new group
            name, ok = QtWidgets.QInputDialog.getText(self, __("Group Name"), __("Enter a name for the new group:"))
            if not ok:
                return
            group.name = name.strip()
            project.add_group(group)

        if group:
            for face in faces:
                self._selectedGroup.remove_face(face)
                group.add_face(face)
            self._detailsGrid.refresh()
            self._refreshGroups()

    @QtCore.Slot(Group)
    def _onRenameGroupTriggered(self, group: Group) -> None:
        """
        Called when the user wants to rename a group.

        Args:
            group (Group): The group to rename.
        """
        name, ok = QtWidgets.QInputDialog.getText(self, __("Group Name"), __("Enter a name for the group:"), text=group.name)
        if ok:
            group.name = name
            self._refreshGroups()
            self._detailsHeader.refresh()
            self._workspace.setDirty()

    @QtCore.Slot(list)
    def _onRemoveFromGroupTriggered(self, faces: list[Face]) -> None:
        """
        Called when the user wants to remove one or more faces from a group.

        Args:
            faces (Face): The faces to remove.
        """
        if len(self._selectedGroup.faces) == len(faces):
            QtWidgets.QMessageBox.warning(self, __("Cannot Remove Face"), __("You cannot remove the last face from a group."))
            return
        newGroup = Group()
        for face in faces:
            self._selectedGroup.remove_face(face)
            newGroup.add_face(face)
        newGroup.recompute_centroid()
        self._workspace.project().add_group(newGroup)
        self._detailsGrid.refresh()
        self._refreshGroups()

    @QtCore.Slot(Group)
    def _onGroupClicked(self, group: Group) -> None:
        """
        Called when the user clicks a group.

        Args:
            group (Group): The group.
        """
        self._selectedGroup = group
        self._detailsGrid.setFaces(group.faces)
        self._detailsHeader.setGroup(group)
        self._groupsGrid.selectGroup(group)

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
        self._detailsGrid.refresh()
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

    @QtCore.Slot(MergeOportunity)
    def _onGroupsMerged(self, mergeOportunity: MergeOportunity) -> None:
        """
        Called when two groups are merged.

        Args:
            mergeOportunity (MergeOportunity): The merge oportunity.
        """
        self._refreshGroups()
        self._workspace.setDirty()

    @QtCore.Slot(MergeOportunity)
    def _onGroupsDontMerged(self, mergeOportunity: MergeOportunity) -> None:
        """
        Called when two groups are not merged.

        Args:
            mergeOportunity (MergeOportunity): The merge oportunity.
        """
        self._workspace.setDirty()
