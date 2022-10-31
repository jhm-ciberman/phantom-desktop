import os

from PySide6 import QtCore, QtGui, QtWidgets

from .PhantomMascotAnimationWidget import PhantomMascotAnimationWidget

from ..ShellWindow import NavigationPage, ShellWindow

from ..Application import Application
from ..Deblur.DeblurPage import DeblurPage
from ..GroupFaces.GroupFacesPage import GroupFacesPage
from ..l10n import __
from ..Models import Image
from ..Perspective.PerspectivePage import PerspectivePage
from ..Widgets.GridBase import GridBase
from .ImageGrid import ImageGrid
from .MainInspectorPanel import MainInspectorPanel
from .. import constants


class ProjectExplorerPage(QtWidgets.QWidget, NavigationPage):
    """
    The main window of the application.
    """

    def __init__(self, shell: ShellWindow, parent=None):
        """
        Initializes the MainWindow class.

        Args:
            shell: The shell window that is used to display the main tab widget.
            parent: The parent widget.
        """
        super().__init__(parent)
        self._shell = shell

        self.setWindowIcon(QtGui.QIcon("res/img/collection.png"))
        self.setWindowTitle(__("Project Explorer"))

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        def makeAction(icon: str, name: str, callback: QtCore.Slot) -> QtGui.QAction:
            action = QtGui.QAction(name, self)
            if icon:
                action.setIcon(QtGui.QIcon("res/img/" + icon))
            action.triggered.connect(callback)
            return action

        self._newProjectAction = makeAction("new_project.png", __("New Project"), self._onNewProjectPressed)
        self._openProjectAction = makeAction("folder.png", __("Open Project..."), self._onOpenProjectPressed)
        self._saveProjectAction = makeAction("save.png", __("Save Project..."), self._onSaveProjectPressed)
        self._saveProjectAsAction = makeAction("save_as.png", __("Save Project As..."), self._onSaveProjectAsPressed)
        self._addImagesAction = makeAction("image_add.png", __("Add Images..."), self._onAddImagesPressed)
        self._addFolderAction = makeAction("folder_add.png", __("Add From Folder..."), self._onAddFolderPressed)
        self._exportImageAction = makeAction("image_save.png", __("Export Image"), self._onExportImagePressed)
        self._correctPerspectiveAction = makeAction("correct_perspective.png", __("Correct Perspective"), self._onCorrectPerspectivePressed)  # noqa: E501
        self._deblurAction = makeAction("deblur.png", __("Deblur Filter"), self._onDeblurPressed)
        self._groupFacesAction = makeAction("group_faces.png", __("Group Similar Faces"), self._onGroupFacesPressed)
        self._selectAllAction = makeAction("", __("Select All"), self._onSelectAllPressed)

        self._editMenu = QtWidgets.QMenu(__("@menubar.edit.header"))
        self._editMenu.addAction(self._correctPerspectiveAction)
        self._editMenu.addAction(self._deblurAction)
        self._editMenu.addAction(self._groupFacesAction)
        self._editMenu.addSeparator()
        self._editMenu.addAction(self._selectAllAction)

        self._viewMenu = QtWidgets.QMenu(__("@menubar.view.header"))
        self._sizePresetActions: list[QtGui.QAction] = []

        for preset in GridBase.sizePresets():
            action = QtGui.QAction(preset.name, self)
            action.setCheckable(True)
            action.setData(preset)
            action.triggered.connect(self._onGridSizePresetPressed)
            self._viewMenu.addAction(action)
            self._sizePresetActions.append(action)

        self._sizePresetActions[1].setChecked(True)

        self._toolbar = QtWidgets.QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self._toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)  # Disable right click menu (wtf Qt?)
        self._toolbar.setIconSize(QtCore.QSize(32, 32))
        self._toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toolbar.setStyleSheet("""QToolBar QToolButton { width: 180px; }""")
        self._toolbar.setOrientation(QtCore.Qt.Orientation.Vertical)

        # self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self._toolbar)
        self._toolbar.addAction(self._newProjectAction)
        self._toolbar.addAction(self._openProjectAction)
        self._toolbar.addAction(self._saveProjectAction)
        self._toolbar.addAction(self._saveProjectAsAction)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._addImagesAction)
        self._toolbar.addAction(self._addFolderAction)
        self._toolbar.addAction(self._exportImageAction)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._correctPerspectiveAction)
        self._toolbar.addAction(self._deblurAction)
        self._toolbar.addAction(self._groupFacesAction)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        splitter.setContentsMargins(10, 10, 10, 10)

        self._stackWidget = QtWidgets.QStackedWidget()

        self._emptyWidget = EmptyProjectMessageWidget(self)
        self._stackWidget.addWidget(self._emptyWidget)

        self._imageGrid = ImageGrid()
        self._imageGrid.imageSelectionChanged.connect(self._onImageGridSelectionChanged)
        self._imageGrid.deblurImagePressed.connect(self._onDeblurPressed)
        self._imageGrid.perspectivePressed.connect(self._onCorrectPerspectivePressed)
        self._stackWidget.addWidget(self._imageGrid)

        self._stackWidget.setCurrentWidget(self._emptyWidget)

        self._inspector = MainInspectorPanel()
        self._inspector.setContentsMargins(0, 0, 0, 0)

        splitter.addWidget(self._stackWidget)
        splitter.addWidget(self._inspector)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(splitter, 1)

        self._onImageGridSelectionChanged()  # Refresh the UI for the first time.

        self._workspace = Application.workspace()
        self._workspace.imagesAdded.connect(self._onImagesAdded)
        self._workspace.imagesRemoved.connect(self._onImagesRemoved)
        self._workspace.projectChanged.connect(self._onProjectChanged)

        self.setAcceptDrops(True)

    def customMenus(self) -> list[QtWidgets.QMenu]:
        return [self._editMenu, self._viewMenu]

    @QtCore.Slot(bool)
    def _onGridSizePresetPressed(self, checked: bool):
        if not checked:
            return
        action = self.sender()
        self._imageGrid.setSizePreset(action.data())
        for a in self._sizePresetActions:
            a.setChecked(a == action)

    @QtCore.Slot()
    def _onImageGridSelectionChanged(self) -> None:
        selectedImages = self._imageGrid.selectedImages()
        self._inspector.setSelectedImages(selectedImages)
        self._shell.setSelectedImages(selectedImages)
        count = len(selectedImages)
        self._exportImageAction.setEnabled(count > 0)
        self._correctPerspectiveAction.setEnabled(count == 1)
        self._deblurAction.setEnabled(count == 1)

    @QtCore.Slot()
    def _onAddImagesPressed(self) -> None:
        Application.projectManager().importImages(self)

    @QtCore.Slot()
    def _onAddFolderPressed(self) -> None:
        Application.projectManager().addFolder(self)

    @QtCore.Slot()
    def _onExportImagePressed(self) -> None:
        selected_images = self._imageGrid.selectedImages()
        Application.projectManager().exportImages(self, selected_images)

    @QtCore.Slot()
    def _onExitPressed(self) -> None:
        Application.instance().quit()

    @QtCore.Slot()
    def _onCorrectPerspectivePressed(self) -> None:
        selected = self._imageGrid.selectedImages()
        if len(selected) == 1:
            self._shell.openPage(PerspectivePage(selected[0]))

    @QtCore.Slot()
    def _onDeblurPressed(self) -> None:
        selected = self._imageGrid.selectedImages()
        if len(selected) == 1:
            self._shell.openPage(DeblurPage(selected[0]))

    @QtCore.Slot()
    def _onGroupFacesPressed(self) -> None:
        if not self._workspace.batchProgress().isFinished:
            QtWidgets.QMessageBox.information(
                self, __("Phantom Desktop is processing images"),
                __("Phantom Desktop is processing images. Please wait until the processing is finished."))
            return

        faces = self._workspace.project().get_faces()
        if len(faces) == 0:
            QtWidgets.QMessageBox.information(
                self, __("No faces found"),
                __("No faces found in the project. Please add images with faces to the project."))
            return

        self._shell.openPage(GroupFacesPage())

    @QtCore.Slot(list)
    def _onImagesAdded(self, images: list[Image]) -> None:
        for image in images:
            self._imageGrid.addImage(image)
        self._onNumberOfImagesChanged()

    @QtCore.Slot(list)
    def _onImagesRemoved(self, images: list[Image]) -> None:
        for image in images:
            self._imageGrid.removeImage(image)
        self._onNumberOfImagesChanged()

    @QtCore.Slot()
    def _onProjectChanged(self) -> None:
        self._imageGrid.clear()
        images = self._workspace.project().images
        for image in images:
            self._imageGrid.addImage(image)
        self._onNumberOfImagesChanged()

    def _onNumberOfImagesChanged(self) -> None:
        imagesCount = len(self._workspace.project().images)
        self._groupFacesAction.setEnabled(imagesCount > 0)
        if imagesCount == 0:
            self._stackWidget.setCurrentWidget(self._emptyWidget)
        else:
            self._stackWidget.setCurrentWidget(self._imageGrid)

    # Drag and drop (User can drag image files, folders and projects onto the window to open them)
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        imagesToAdd = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                extension = os.path.splitext(path)[1].lower()
                extension = extension[1:] if extension.startswith(".") else extension
                if extension == constants.app_project_extension:
                    Application.projectManager().openProject(self, path)
                    break  # Only one project can be opened at a time
                elif extension in constants.app_import_extensions:
                    imagesToAdd.append(path)
            elif os.path.isdir(path):
                Application.projectManager().addFolder(self, path)
                # TODO: support adding multiple folders at once
                break
        if len(imagesToAdd) > 0:
            images = [Image(path) for path in imagesToAdd]
            Application.projectManager().addImagesToProject(self, images)

    @QtCore.Slot()
    def _onSelectAllPressed(self) -> None:
        self._imageGrid.selectAll()

    @QtCore.Slot()
    def _onNewProjectPressed(self) -> None:
        Application.projectManager().newProject(self)

    @QtCore.Slot()
    def _onOpenProjectPressed(self) -> None:
        Application.projectManager().openProject(self)

    @QtCore.Slot()
    def _onSaveProjectPressed(self) -> None:
        Application.projectManager().saveProject(self)

    @QtCore.Slot()
    def _onSaveProjectAsPressed(self) -> None:
        Application.projectManager().saveProjectAs(self)


class EmptyProjectMessageWidget(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        contentWidget = QtWidgets.QWidget(self)
        contentWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._layout = QtWidgets.QVBoxLayout(contentWidget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)
        self._layout.setAlignment(QtCore.Qt.AlignCenter)

        self._phantomMascotAnimation = PhantomMascotAnimationWidget(self)
        self._layout.addWidget(self._phantomMascotAnimation)

        self._layout.addSpacing(40)

        self._title = QtWidgets.QLabel(__("The project is empty"))
        self._title.setAlignment(QtCore.Qt.AlignCenter)
        self._title.setStyleSheet("font-size: 24px;")
        self._layout.addWidget(self._title)

        self._subtitle = QtWidgets.QLabel(__("Drag images here to start"))
        self._subtitle.setAlignment(QtCore.Qt.AlignCenter)
        self._subtitle.setStyleSheet("font-size: 16px; color: #666;")
        self._layout.addWidget(self._subtitle)

        self._layout.addSpacing(40)

        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(buttonsLayout)

        self._addImageButton = QtWidgets.QPushButton(QtGui.QIcon("res/img/image_add.png"), __("Add Images"))
        self._addImageButton.setIconSize(QtCore.QSize(32, 32))
        self._addImageButton.clicked.connect(self._onAddImagesPressed)

        self._addFolderButton = QtWidgets.QPushButton(QtGui.QIcon("res/img/folder_add.png"), __("Add From Folder"))
        self._addFolderButton.setIconSize(QtCore.QSize(32, 32))
        self._addFolderButton.clicked.connect(self._onAddFolderPressed)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self._addImageButton, 1)
        buttonsLayout.addWidget(self._addFolderButton, 1)
        buttonsLayout.addStretch()

        self._layout.addSpacing(20)

        rtfmLayout = QtWidgets.QHBoxLayout()
        rtfmLayout.setSpacing(5)
        self._layout.addLayout(rtfmLayout)

        self._rtfmLabel = QtWidgets.QLabel(__("Don't know where to start?"))
        self._rtfmLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._rtfmLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._rtfmLabel.setStyleSheet("font-size: 16px; color: #666;")
        rtfmLayout.addWidget(self._rtfmLabel, 0)

        self._rtfmButton = QtWidgets.QPushButton(__("Check the online help"))
        self._rtfmButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._rtfmButton.clicked.connect(self._onRTFMPressed)
        rtfmLayout.addWidget(self._rtfmButton, 0)

        frameLayout = QtWidgets.QVBoxLayout(self)
        frameLayout.setContentsMargins(0, 0, 0, 0)
        frameLayout.addWidget(contentWidget, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(frameLayout)

    @QtCore.Slot()
    def _onAddImagesPressed(self) -> None:
        Application.projectManager().importImages(self)

    @QtCore.Slot()
    def _onAddFolderPressed(self) -> None:
        Application.projectManager().addFolder(self)

    @QtCore.Slot()
    def _onRTFMPressed(self) -> None:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(constants.app_docs_url))
