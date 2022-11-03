from PySide6 import QtCore, QtWidgets, QtGui
import os

from ..Main.PhantomMascotAnimationWidget import PhantomMascotFacesAnimation
from ..Workspace import Workspace
from .HtmlReportExporter import HtmlReportExporter
from ..ShellWindow import NavigationPage
from .FaceInspectorPanel import FaceInspectorPanel
from ..Application import Application
from ..l10n import __
from ..Models import Face, Group, Image
from .GroupDetailsGrid import GroupDetailsGrid
from .GroupDetailsHeader import GroupDetailsHeaderWidget
from .GroupSelector import GroupSelector, MultiGroupSelector
from .GroupMasterGrid import GroupMasterGrid
from .MergingWizard import MergingWizard


class GroupFacesPageEmpty(QtWidgets.QWidget):
    """
    A fullscreen widget that shows when there are no groups to display.
    This shows a button to "Group Faces" and a message that there are no faces to display.
    """

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(layout)

        self._phantomMascotAnimation = PhantomMascotFacesAnimation(self)
        layout.addWidget(self._phantomMascotAnimation)

        layout.addSpacing(40)

        self._title = QtWidgets.QLabel(__("Group faces"))
        self._title.setAlignment(QtCore.Qt.AlignCenter)
        self._title.setStyleSheet("font-size: 24px;")
        layout.addWidget(self._title)

        self._subtitle = QtWidgets.QLabel(__("Add all the images you want to the project and click the button below to start"))
        self._subtitle.setAlignment(QtCore.Qt.AlignCenter)
        self._subtitle.setWordWrap(True)
        self._subtitle.setContentsMargins(40, 0, 40, 0)
        self._subtitle.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(self._subtitle)

        layout.addSpacing(40)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setAlignment(QtCore.Qt.AlignCenter)
        layout.addLayout(buttonLayout)

        self.button = QtWidgets.QPushButton(QtGui.QIcon("res/img/face.png"), __("Group Faces"))
        self.button.setIconSize(QtCore.QSize(32, 32))
        self.button.setStyleSheet("padding-left: 16px; padding-right: 16px;")
        self.button.clicked.connect(self._onGroupFacesClicked)
        buttonLayout.addWidget(self.button)

    @QtCore.Slot()
    def _onGroupFacesClicked(self) -> None:
        Application.workspace().recalculateGroups()


class GroupFacesPageContent(QtWidgets.QWidget):
    """
    This is the main widget in the GroupFacesPage.
    """
    _selectedGroup: Group = None

    _selectedFaces: list[Face] = []

    _workspace: Workspace = None

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._workspace = Application.workspace()
        self._workspace.imagesAdded.connect(self._onImagesAdded)
        self._workspace.imagesRemoved.connect(self._onImageRemoved)
        self._workspace.imageProcessed.connect(self._onImageProcessed)
        self._workspace.groupsChanged.connect(self._onGroupsChanged)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        splitter.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(splitter)

        leftColumnWidget = QtWidgets.QWidget()
        leftColumnLayout = QtWidgets.QVBoxLayout()
        leftColumnLayout.setContentsMargins(0, 0, 0, 0)
        leftColumnWidget.setLayout(leftColumnLayout)
        splitter.addWidget(leftColumnWidget)

        self._hasGroups = len(self._workspace.project().groups) > 0
        self._mergingWizard = MergingWizard(self._workspace, leftColumnWidget)
        leftColumnLayout.addWidget(self._mergingWizard)

        self._groupsGrid = GroupMasterGrid()
        leftColumnLayout.addWidget(self._groupsGrid)

        detailsWidget = QtWidgets.QWidget()
        detailsLayout = QtWidgets.QVBoxLayout()
        detailsLayout.setContentsMargins(0, 0, 0, 0)
        detailsWidget.setLayout(detailsLayout)

        self._detailsHeader = GroupDetailsHeaderWidget()
        self._detailsGrid = GroupDetailsGrid()

        detailsLayout.addWidget(self._detailsHeader)
        detailsLayout.addWidget(self._detailsGrid)
        splitter.addWidget(detailsWidget)

        self._inspector = FaceInspectorPanel()
        splitter.addWidget(self._inspector)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

        self._groupsGrid.groupClicked.connect(self._onGroupClicked)
        self._groupsGrid.renameGroupTriggered.connect(self._onRenameGroupTriggered)
        self._groupsGrid.combineGroupTriggered.connect(self._onCombineGroupTriggered)

        self._detailsGrid.selectedFacesChanged.connect(self._onSelectedFacesChanged)
        self._detailsGrid.moveToGroupTriggered.connect(self._onMoveToGroupTriggered)
        self._detailsGrid.removeFromGroupTriggered.connect(self._onRemoveFromGroupTriggered)
        self._detailsGrid.useAsMainFaceTriggered.connect(self._onUseAsMainFaceTriggered)
        self._detailsHeader.renameGroupTriggered.connect(self._onRenameGroupTriggered)
        self._detailsHeader.combineGroupTriggered.connect(self._onCombineGroupTriggered)

        # Connect signals
        self.groupsMenu = QtWidgets.QMenu(__("Groups"))
        self._renameGroupAction = self.groupsMenu.addAction(
            QtGui.QIcon("res/img/edit.png"), __("Rename Group..."), self._onRenameGroupActionTriggered)
        self._combineGroupAction = self.groupsMenu.addAction(__("Combine Group..."), self._onCombineGroupActionTriggered)
        self.groupsMenu.addSeparator()
        self._exportAsHtmlAction = self.groupsMenu.addAction(__("Export as HTML..."), self._onExportAsHtmlTriggered)
        self.groupsMenu.addSeparator()
        self._recalculateGroupsAction = self.groupsMenu.addAction(__("Delete all groups"), self._onDeleteAllGroupsTriggered)

        self.facesMenu = QtWidgets.QMenu(__("Faces"))
        self._moveToGroupAction = self.facesMenu.addAction(__("Move to Group..."), self._onMoveToGroupActionTriggered)
        self._removeFromGroupAction = self.facesMenu.addAction(__("Remove from Group..."), self._onRemoveFromGroupActionTriggered)  # noqa
        self._useAsMainFaceAction = self.facesMenu.addAction(__("Use as Main Face"), self._onUseAsMainFaceActionTriggered)

        self.refreshGroups()

    @QtCore.Slot()
    def _onGroupsChanged(self):
        self.refreshGroups()

        hasGroupsNow = len(self._workspace.project().groups) > 0
        if self._hasGroups != hasGroupsNow:
            self._mergingWizard.recalculateMergeOpportunities()
            self._hasGroups = hasGroupsNow

    @QtCore.Slot(Image)
    def _onImageProcessed(self, image: Image) -> None:
        """
        Called when an image is processed.
        """
        project = self._workspace.project()
        for face in image.faces:
            project.add_face_to_best_group(face)

    def refreshGroups(self) -> None:
        groups = self._workspace.project().groups
        self._groupsGrid.setGroups(groups)
        if self._selectedGroup is None and len(self._groupsGrid.groups()) > 0:
            self._onGroupClicked(groups[0])

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
        self.refreshGroups()

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
        self.refreshGroups()

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
            self.refreshGroups()

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
            self.refreshGroups()
            self._detailsHeader.refresh()
            self._workspace.setDirty()

    @QtCore.Slot(Group)
    def _onRenameGroupActionTriggered(self) -> None:
        """
        Called when the user wants to rename the selected group.
        """
        if self._selectedGroup is not None:
            self._onRenameGroupTriggered(self._selectedGroup)

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
        self.refreshGroups()

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
    def _onUseAsMainFaceTriggered(self, face: Face) -> None:
        """
        Called when the user wants to use a face as the main face.

        Args:
            face (Face): The face.
        """
        self._selectedGroup.main_face_override = face
        self._detailsGrid.refresh()
        self._detailsHeader.refresh()
        self.refreshGroups()
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
            self.refreshGroups()
            self._workspace.setDirty()

    @QtCore.Slot()
    def _onCombineGroupActionTriggered(self) -> None:
        """
        Called when the user wants to combine the selected group with another group.
        """
        if self._selectedGroup is not None:
            self._onCombineGroupTriggered(self._selectedGroup)

    @QtCore.Slot(list)
    def _onSelectedFacesChanged(self, faces: list[Face]) -> None:
        """
        Called when the selected faces change.

        Args:
            faces (list[Face]): The selected faces.
        """
        self._selectedFaces = faces
        self._inspector.setSelectedFaces(faces)

        # Update actions
        self._removeFromGroupAction.setEnabled(len(faces) > 0)
        self._moveToGroupAction.setEnabled(len(faces) > 0)
        self._useAsMainFaceAction.setEnabled(len(faces) == 1 and self._selectedGroup is not None)

    @QtCore.Slot()
    def _onExportAsHtmlTriggered(self) -> None:
        """
        Called when the user wants to export the groups as HTML.
        """
        project = self._workspace.project()
        if not project.groups:
            QtWidgets.QMessageBox.warning(self, __("No Groups"), __("There are no groups to export."))
            return

        groupsToExport = MultiGroupSelector.getGroups(project.groups, self, __("Select the groups to export"))
        if not groupsToExport:
            return

        defaultFilename = os.path.splitext(os.path.basename(project.path))[0] + ".html"
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, __("Export as HTML"), defaultFilename, "HTML (*.html)")
        if filename:
            folder = os.path.dirname(filename)

            if os.path.exists(folder) and os.listdir(folder):
                if not QtWidgets.QMessageBox.question(
                        self, __("Folder not empty"), __("The folder is not empty. Do you want to continue?")):
                    return

            exporter = HtmlReportExporter(groupsToExport, filename)
            exporter.export()

            # Ask the user if they want to open the file
            if QtWidgets.QMessageBox.question(
                    self,
                    __("HTML Report exported successfully"),
                    __("The HTML report was exported successfully. Do you want to open it?")):
                Application.projectManager().openFileExternally(filename)

    @QtCore.Slot()
    def _onDeleteAllGroupsTriggered(self) -> None:
        """
        Called when the user wants to recalculate the groups.
        """
        # Ask the user if he wants to continue because this will delete all the groups
        if not QtWidgets.QMessageBox.question(
                self,
                __("Delete all groups"),
                __("This will delete all the groups. After that you can run the group detection again. Do you want to continue?")):  # noqa: E501
            return

        self._workspace.clearGroups()

    @QtCore.Slot()
    def _onMoveToGroupActionTriggered(self) -> None:
        """
        Called when the user wants to move the selected faces to a group.
        """
        if len(self._selectedFaces) > 0:
            self._onMoveToGroupTriggered(self._selectedFaces)

    @QtCore.Slot()
    def _onRemoveFromGroupActionTriggered(self) -> None:
        """
        Called when the user wants to remove the selected faces from a group.
        """
        if len(self._selectedFaces) > 0:
            self._onRemoveFromGroupTriggered(self._selectedFaces)

    @QtCore.Slot()
    def _onUseAsMainFaceActionTriggered(self) -> None:
        """
        Called when the user wants to use the selected face as the main face.
        """
        if len(self._selectedFaces) == 1:
            self._onUseAsMainFaceTriggered(self._selectedFaces[0])


class GroupFacesPage(QtWidgets.QWidget, NavigationPage):
    """
    A window that allows the user to group faces.
    """

    _workspace: Workspace

    def __init__(self) -> None:
        """
        Initialize a new instance of the GroupFacesWindow class.
        """
        super().__init__()
        self._workspace = Application.workspace()
        self._workspace.groupsChanged.connect(self._onGroupsChanged)

        self.setWindowIcon(QtGui.QIcon("res/img/group_faces.png"))
        self.setWindowTitle(__("Group Faces"))

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._stack = QtWidgets.QStackedWidget()
        layout.addWidget(self._stack)

        self._emptyPage = GroupFacesPageEmpty()
        self._stack.addWidget(self._emptyPage)

        self._content = GroupFacesPageContent()
        self._stack.addWidget(self._content)

        self._onGroupsChanged()

    def customMenus(self) -> list[QtWidgets.QMenu]:
        return [self._content.groupsMenu, self._content.facesMenu]

    @QtCore.Slot()
    def _onGroupsChanged(self) -> None:
        """
        Called when the groups change.
        """
        groups = self._workspace.project().groups
        if len(groups) == 0:
            self._stack.setCurrentWidget(self._emptyPage)
            self._content.groupsMenu.setEnabled(False)
            self._content.facesMenu.setEnabled(False)
        else:
            self._stack.setCurrentWidget(self._content)
            self._content.groupsMenu.setEnabled(True)
            self._content.facesMenu.setEnabled(True)
