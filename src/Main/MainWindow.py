from PySide6 import QtGui, QtCore, QtWidgets
from ..Workspace import BatchProgress
from ..Application import Application
from .InspectorPanel import InspectorPanel
from ..Widgets.GridBase import GridBase
from ..QtHelpers import setSplitterStyle
from .ImageGrid import ImageGrid
from ..Models import Image
from ..Perspective.PerspectiveWindow import PerspectiveWindow
from ..Deblur.DeblurWindow import DeblurWindow
from ..GroupFaces.GroupFacesWindow import GroupFacesWindow
import glob
import os
from src.l10n import __


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window of the application.
    """

    def __init__(self):
        """
        Initializes the MainWindow class.
        """
        super().__init__()

        self.setWindowTitle("Phantom")
        self.setMinimumSize(800, 600)

        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().setFixedHeight(20)

        self._progressBar = QtWidgets.QProgressBar()
        self._progressBar.setFixedHeight(20)
        self._progressBar.setFixedWidth(200)
        self._progressBar.setValue(0)
        self._progressBar.setVisible(False)
        self._progressBar.setTextVisible(False)
        # self._progressBar.setGeometry(30, 40, 200, 25)
        self.statusBar().addPermanentWidget(self._progressBar)

        mainWidget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._addImagesAction = QtGui.QAction(
            QtGui.QIcon("res/image_add.png"), __("Add Images"), self)
        self._addImagesAction.setToolTip(__("Add images to current project"))
        self._addImagesAction.triggered.connect(self._onAddImagesPressed)

        self._addFolderAction = QtGui.QAction(
            QtGui.QIcon("res/folder_add.png"), __("Add From Folder"), self)
        self._addFolderAction.setToolTip(__("Add images from folder to current project"))
        self._addFolderAction.triggered.connect(self._onAddFolderPressed)

        self._exportImageAction = QtGui.QAction(
            QtGui.QIcon("res/image_save.png"), __("Export Image"), self)
        self._exportImageAction.setEnabled(False)
        self._exportImageAction.triggered.connect(self._onExportImagePressed)

        self._correctPerspectiveAction = QtGui.QAction(
            QtGui.QIcon("res/correct_perspective.png"), __("Correct Perspective"), self)
        self._correctPerspectiveAction.setEnabled(False)
        self._correctPerspectiveAction.triggered.connect(self._onCorrectPerspectivePressed)

        self._deblurAction = QtGui.QAction(
            QtGui.QIcon("res/deblur.png"), __("Deblur Filter"), self)
        self._deblurAction.setEnabled(False)
        self._deblurAction.triggered.connect(self._onDeblurPressed)

        self._groupFacesAction = QtGui.QAction(
            QtGui.QIcon("res/group_faces.png"), __("Group Similar Faces"), self)
        self._groupFacesAction.setEnabled(False)
        self._groupFacesAction.triggered.connect(self._onGroupFacesPressed)

        self._newProjectAction = QtGui.QAction(
            QtGui.QIcon("res/new_project.png"), __("New Project"), self)
        self._newProjectAction.setShortcut("Ctrl+N")
        self._newProjectAction.triggered.connect(self._onNewProjectPressed)

        self._openProjectAction = QtGui.QAction(
            QtGui.QIcon("res/open.png"), __("Open Project..."), self)
        self._openProjectAction.setShortcut("Ctrl+O")
        self._openProjectAction.triggered.connect(self._onOpenProjectPressed)

        self._saveProjectAction = QtGui.QAction(
            QtGui.QIcon("res/save.png"), __("Save Project..."), self)
        self._saveProjectAction.setEnabled(False)
        self._saveProjectAction.setShortcut("Ctrl+S")
        self._saveProjectAction.triggered.connect(self._onSaveProjectPressed)

        self._saveProjectAsAction = QtGui.QAction(
            QtGui.QIcon("res/save_as.png"), __("Save Project As..."), self)
        self._saveProjectAsAction.setEnabled(False)
        self._saveProjectAsAction.setShortcut("Ctrl+Shift+S")
        self._saveProjectAsAction.triggered.connect(self._onSaveProjectAsPressed)

        self._exitAction = QtGui.QAction(
            QtGui.QIcon("res/exit.png"), __("Exit"), self)
        self._exitAction.setShortcut("Ctrl+Q")
        self._exitAction.triggered.connect(self.close)

        self._toolbar = QtWidgets.QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self._toolbar.setIconSize(QtCore.QSize(48, 48))
        self._toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toolbar.addAction(self._openProjectAction)
        self._toolbar.addAction(self._saveProjectAction)
        self._toolbar.addAction(self._saveProjectAsAction)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._addImagesAction)
        self._toolbar.addAction(self._addFolderAction)
        self._toolbar.addAction(self._exportImageAction)
        self._toolbar.addAction(self._correctPerspectiveAction)
        self._toolbar.addAction(self._deblurAction)
        self._toolbar.addAction(self._groupFacesAction)
        self._toolbar.setStyleSheet("""QToolBar QToolButton { width: 200px; }""")
        self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self._toolbar)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        splitter.setContentsMargins(10, 10, 10, 10)
        setSplitterStyle(splitter)

        self._imageGrid = ImageGrid()
        self._imageGrid.selectionChanged.connect(self._onImageGridSelectionChanged)

        self.inspector_panel = InspectorPanel()
        self.inspector_panel.setContentsMargins(0, 0, 0, 0)

        splitter.addWidget(self._imageGrid)
        splitter.addWidget(self.inspector_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        self._layout.addWidget(splitter, 1)
        mainWidget.setLayout(self._layout)
        self.setCentralWidget(mainWidget)

        self._menuBar = self.menuBar()
        self._fileMenu = self._menuBar.addMenu(__("&File"))
        self._fileMenu.addAction(self._newProjectAction)
        self._fileMenu.addAction(self._openProjectAction)
        self._fileMenu.addAction(self._saveProjectAction)
        self._fileMenu.addAction(self._saveProjectAsAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._addImagesAction)
        self._fileMenu.addAction(self._addFolderAction)
        self._fileMenu.addAction(self._exportImageAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._exitAction)

        self._editMenu = self._menuBar.addMenu(__("&Edit"))
        self._editMenu.addAction(self._correctPerspectiveAction)
        self._editMenu.addAction(self._deblurAction)
        self._editMenu.addAction(self._groupFacesAction)

        self._viewMenu = self._menuBar.addMenu(__("&View"))
        self._sizePresetActions = []

        for preset in GridBase.sizePresets():
            action = QtGui.QAction(preset.name, self)
            action.setCheckable(True)
            action.setData(preset)
            action.triggered.connect(self._onGridSizePresetPressed)
            self._viewMenu.addAction(action)
            self._sizePresetActions.append(action)

        self._sizePresetActions[1].setChecked(True)

        # Only because GC closes the window when the reference is lost.
        self._childWindows = []  # type: list[QtWidgets.QWidget]

        self._onImageGridSelectionChanged()  # Refresh the UI for the first time.

        self._workspace = Application.workspace()
        self._workspace.batchProgressChanged.connect(self._onBatchProgressChanged)
        self._workspace.imageAdded.connect(self._onImageAdded)
        self._workspace.imageRemoved.connect(self._onImageRemoved)
        self._workspace.projectChanged.connect(self._onProjectChanged)
        self._workspace.isDirtyChanged.connect(self._onIsDirtyChanged)

        # for image_path in self._getTestImagePaths():
        #     self._addImage(image_path)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:

        if self._workspace.isDirty():
            reply = QtWidgets.QMessageBox.question(
                self, __("Save Project"), __("Do you want to save the project before closing? Unsaved changes will be lost."),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

            if reply == QtWidgets.QMessageBox.Yes:
                self._onSaveProjectPressed()
            elif reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return

        self._workspace.closeProject()
        super().closeEvent(event)

    @QtCore.Slot(bool)
    def _onGridSizePresetPressed(self, checked):
        if not checked:
            return
        action = self.sender()
        self._imageGrid.setSizePreset(action.data())
        for a in self._sizePresetActions:
            a.setChecked(a == action)

    def _getTestImagePaths(self):
        max_image_count = 2000
        image_paths = [
            "test_images/icon.png",
            "test_images/billboard.jpg",
            "test_images/cookies-800x400.jpg",
            "test_images/lena.png",
            "test_images/lena_blur_3.png",
            "test_images/lena_blur_10.png",
            "test_images/endgame.jpg",
        ]
        image_paths += glob.glob("test_images/exif/**/*.jpg", recursive=True)
        image_paths += glob.glob("test_images/exif/**/*.tiff", recursive=True)
        image_paths += glob.glob("test_images/celebrities/**/*.jpg", recursive=True)

        return image_paths[:max_image_count]

    @QtCore.Slot()
    def _onImageGridSelectionChanged(self) -> None:
        selected_images = self._imageGrid.selectedImages()
        self.inspector_panel.setSelectedImages(selected_images)
        count = len(selected_images)
        if (count == 0):
            self.statusBar().showMessage(__("{count} images in the collection", count=len(self._imageGrid.images())))
        elif (count == 1):
            self.statusBar().showMessage(selected_images[0].full_path)
        else:
            self.statusBar().showMessage(__("{count} images selected", count=count))

        self._exportImageAction.setEnabled(count > 0)
        self._correctPerspectiveAction.setEnabled(count == 1)
        self._deblurAction.setEnabled(count == 1)

    @QtCore.Slot()
    def _onAddImagesPressed(self) -> None:
        file_paths, _filter = QtWidgets.QFileDialog.getOpenFileNames(
            self, __("Select Images to the project"), "", __("Images") + " (*.jpg *.jpeg *.png *.tiff *.tif *.bmp)")

        for file_path in file_paths:
            self._addImage(file_path)

    @QtCore.Slot()
    def _onAddFolderPressed(self) -> None:
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, __("Select a folder to add to the project"), "", QtWidgets.QFileDialog.ShowDirsOnly)

        if folder_path:
            extensions = ["png", "jpg", "jpeg", "tiff", "tif", "bmp"]
            glob_base = folder_path + "/**/*."
            file_paths = []
            for ext in extensions:
                file_paths += glob.glob(glob_base + ext, recursive=True)

            # Show a dialog asking the user to confirm the files to add.
            count = len(file_paths)
            if count == 0:
                QtWidgets.QMessageBox.warning(
                    self, __("No images found"),
                    __("No images found in the selected folder. Please select a folder with images."))
                return
            else:
                result = QtWidgets.QMessageBox.question(
                    self, __("Add images to the project"),
                    __("Found {count} images in the selected folder. Do you want to add them to the project?", count=count),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

                if result == QtWidgets.QMessageBox.No:
                    return

            for file_path in file_paths:
                self._addImage(file_path)

    @QtCore.Slot()
    def _onExportImagePressed(self) -> None:
        selected_images = self._imageGrid.selectedImages()
        if len(selected_images) == 1:
            file_path, _filter = QtWidgets.QFileDialog.getSaveFileName(
                self, __("Export Image"), selected_images[0].full_path, __("Images") + " (*.jpg *.jpeg *.png)")
            if file_path:
                selected_images[0].save(file_path)
        else:
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                self, __("Select a folder to export images to"), "", QtWidgets.QFileDialog.ShowDirsOnly)

            if folder_path:
                for image in selected_images:
                    image.save(os.path.join(folder_path, image.name))

    @QtCore.Slot()
    def _onCorrectPerspectivePressed(self) -> None:
        selected = self._imageGrid.selectedImages()
        if len(selected) == 1:
            window = PerspectiveWindow(selected[0])
            self._childWindows.append(window)
            window.showMaximized()

    @QtCore.Slot()
    def _onDeblurPressed(self) -> None:
        selected = self._imageGrid.selectedImages()
        if len(selected) == 1:
            window = DeblurWindow(selected[0])
            self._childWindows.append(window)
            window.showMaximized()

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

        window = GroupFacesWindow()
        self._childWindows.append(window)
        window.showMaximized()

    def _addImage(self, image_path: str) -> None:
        image = None
        try:
            image = Image(image_path)
        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")

        if image:
            self._workspace.addImage(image)

    @QtCore.Slot()
    def _onImageAdded(self, image: Image) -> None:
        self._imageGrid.addImage(image)
        self._onNumberOfImagesChanged()

    @QtCore.Slot()
    def _onImageRemoved(self, image: Image) -> None:
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
        self._imageGrid.setEnabled(imagesCount > 0)

    @QtCore.Slot(BatchProgress)
    def _onBatchProgressChanged(self, batch: BatchProgress) -> None:
        self._progressBar.setValue(batch.progress * 100)

        if batch.total == 0:
            self._progressBar.setVisible(False)
            pass
        elif batch.value == batch.total:
            self._progressBar.setVisible(False)
            self.statusBar().showMessage(__("Processing finished"))
        else:
            self.statusBar().showMessage(__("Processing images {value}/{total}", value=batch.value, total=batch.total))
            self._progressBar.setVisible(True)

    @QtCore.Slot()
    def _onOpenProjectPressed(self) -> None:
        file_path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select a project file", "", "Phantom Project (*.phantom)")

        if file_path:
            self._workspace.openProject(file_path)

    @QtCore.Slot()
    def _onNewProjectPressed(self) -> None:
        if self._workspace.isDirty():
            result = QtWidgets.QMessageBox.question(
                self, __("New project"), __("The current project has unsaved changes. Do you want to continue?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

            if result == QtWidgets.QMessageBox.No:
                return

        self._workspace.newProject()

    @QtCore.Slot()
    def _onSaveProjectPressed(self) -> None:
        if self._workspace.project().is_empty:
            return

        if self._workspace.project().file_path:
            self._workspace.saveProject()
        else:
            self._onSaveProjectAsPressed()

    @QtCore.Slot()
    def _onSaveProjectAsPressed(self) -> None:
        if self._workspace.project().is_empty:
            return
        current_path = self._workspace.project().file_path
        file_dir = os.path.dirname(current_path) if current_path else ""

        file_path, _filter = QtWidgets.QFileDialog.getSaveFileName(
            self, __("Save project"), file_dir, __("Phantom Project") + " (*.phantom)")

        if file_path:
            self._workspace.saveProject(file_path)

    @QtCore.Slot(bool)
    def _onIsDirtyChanged(self, is_dirty: bool) -> None:
        self._saveProjectAction.setEnabled(is_dirty)
        self._saveProjectAsAction.setEnabled(is_dirty)
