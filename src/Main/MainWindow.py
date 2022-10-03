from PySide6 import QtGui, QtCore, QtWidgets

from ..Application import Application
from ..ProjectFile import ProjectFileWriter, ProjectFileReader
from .InspectorPanel import InspectorPanel
from ..EventBus import EventBus
from ..Widgets.GridBase import GridBase
from ..ImageFeaturesService import ImageFeaturesService
from ..QtHelpers import setSplitterStyle
from .ImageGrid import ImageGrid
from ..Models import Image, Project
from ..Perspective.PerspectiveWindow import PerspectiveWindow
from ..Deblur.DeblurWindow import DeblurWindow
from ..GroupFaces.GroupFacesWindow import GroupFacesWindow
import glob
import os


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
        self.statusBar().showMessage("Phantom Desktop")

        self._progressBar = QtWidgets.QProgressBar()
        self._progressBar.setFixedHeight(20)
        self._progressBar.setFixedWidth(200)
        self._progressBar.setValue(0)
        self._progressBar.setVisible(False)
        self._progressBar.setTextVisible(False)
        # self._progressBar.setGeometry(30, 40, 200, 25)
        self.statusBar().addPermanentWidget(self._progressBar)

        # We keep a count of how many items were queues for processing since
        # the last time the progress bar finished. We only reset this number
        # to 0 when the progress bar finishes.
        self._itemsQueuedCount = 0
        self._itemsProcessedCount = 0

        mainWidget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._addImagesAction = QtGui.QAction(
            QtGui.QIcon("res/image_add.png"), "Add Images", self)
        self._addImagesAction.setToolTip("Add images to current project")
        self._addImagesAction.triggered.connect(self._onAddImagesPressed)

        self._addFolderAction = QtGui.QAction(
            QtGui.QIcon("res/folder_add.png"), "Add From Folder", self)
        self._addFolderAction.setToolTip("Add images from folder to current project")
        self._addFolderAction.triggered.connect(self._onAddFolderPressed)

        self._exportImageAction = QtGui.QAction(
            QtGui.QIcon("res/image_save.png"), "Export Image", self)
        self._exportImageAction.triggered.connect(self._onExportImagePressed)

        self._correctPerspectiveAction = QtGui.QAction(
            QtGui.QIcon("res/correct_perspective.png"), "Correct Perspective", self)
        self._correctPerspectiveAction.triggered.connect(self._onCorrectPerspectivePressed)

        self._deblurAction = QtGui.QAction(
            QtGui.QIcon("res/deblur.png"), "Deblur Filter", self)
        self._deblurAction.triggered.connect(self._onDeblurPressed)

        self._groupFacesAction = QtGui.QAction(
            QtGui.QIcon("res/group_faces.png"), "Group Similar Faces", self)
        self._groupFacesAction.triggered.connect(self._onGroupFacesPressed)

        self._exitAction = QtGui.QAction(
            QtGui.QIcon("res/exit.png"), "Exit", self)
        self._exitAction.triggered.connect(self.close)

        self._saveProjectAction = QtGui.QAction(
            QtGui.QIcon("res/save.png"), "Save Project...", self)
        self._saveProjectAction.triggered.connect(self._onSaveProjectPressed)

        self._saveProjectAsAction = QtGui.QAction(
            QtGui.QIcon("res/save_as.png"), "Save Project As...", self)
        self._saveProjectAsAction.triggered.connect(self._onSaveProjectAsPressed)

        self._openProjectAction = QtGui.QAction(
            QtGui.QIcon("res/open.png"), "Open Project...", self)
        self._openProjectAction.triggered.connect(self._onOpenProjectPressed)

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
        self._fileMenu = self._menuBar.addMenu("&File")
        self._fileMenu.addAction(self._openProjectAction)
        self._fileMenu.addAction(self._saveProjectAction)
        self._fileMenu.addAction(self._saveProjectAsAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._addImagesAction)
        self._fileMenu.addAction(self._addFolderAction)
        self._fileMenu.addAction(self._exportImageAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self._exitAction)

        self._editMenu = self._menuBar.addMenu("&Edit")
        self._editMenu.addAction(self._correctPerspectiveAction)
        self._editMenu.addAction(self._deblurAction)
        self._editMenu.addAction(self._groupFacesAction)

        self._viewMenu = self._menuBar.addMenu("&View")
        self._sizePresetActions = []

        for preset in GridBase.sizePresets():
            action = QtGui.QAction(preset.name + " Thumbnails", self)
            action.setCheckable(True)
            action.setData(preset)
            action.triggered.connect(self._onGridSizePresetPressed)
            self._viewMenu.addAction(action)
            self._sizePresetActions.append(action)

        self._sizePresetActions[1].setChecked(True)

        # Only because GC closes the window when the reference is lost.
        self._childWindows = []  # type: list[QtWidgets.QWidget]

        self._onImageGridSelectionChanged()  # Refresh the UI for the first time.

        EventBus.default().imageProcessed.connect(self._onImageProcessed)
        EventBus.default().imageProcessingFailed.connect(self._onImageProcessingFailed)
        ImageFeaturesService.instance().start()

        # for image_path in self._getTestImagePaths():
        #     self._addImage(image_path)

    def project(self) -> Project:
        """
        Returns the current open project.
        """
        return Application.instance().currentProject()

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
            self.statusBar().showMessage("{} images in the collection".format(len(self._imageGrid.images())))
        elif (count == 1):
            self.statusBar().showMessage(selected_images[0].full_path)
        else:
            self.statusBar().showMessage("{} images selected".format(count))

        self._exportImageAction.setEnabled(count > 0)
        self._correctPerspectiveAction.setEnabled(count == 1)
        self._deblurAction.setEnabled(count == 1)
        self._groupFacesAction.setEnabled(count > 1 or count == 0)

    @QtCore.Slot()
    def _onAddImagesPressed(self) -> None:
        file_paths, _filter = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select Images to the project", "", "Images (*.png *.jpg *.jpeg *.tiff)")

        for file_path in file_paths:
            self._addImage(file_path)

    @QtCore.Slot()
    def _onAddFolderPressed(self) -> None:
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select a folder to add to the project", "")

        if folder_path:
            extensions = ["png", "jpg", "jpeg", "tiff"]
            glob_base = folder_path + "/**/*."
            file_paths = []
            for ext in extensions:
                file_paths += glob.glob(glob_base + ext, recursive=True)

            # Show a dialog asking the user to confirm the files to add.
            count = len(file_paths)
            if count == 0:
                QtWidgets.QMessageBox.warning(
                    self, "No images found", "No images found in the selected folder. Please select a folder with images.")
                return
            else:
                result = QtWidgets.QMessageBox.question(
                    self, f"{count} images found", f"{count} images found in the selected folder. "
                    "Do you want to add them to the project?")
                if result != QtWidgets.QMessageBox.Yes:
                    return

            for file_path in file_paths:
                self._addImage(file_path)

    @QtCore.Slot()
    def _onExportImagePressed(self) -> None:
        selected_images = self._imageGrid.selectedImages()
        if len(selected_images) == 1:
            file_path, _filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save File", "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                selected_images[0].save(file_path)
        else:
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select a folder to export the images to", "")

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
        selected = self._imageGrid.selectedImages()
        if len(selected) == 1:
            return

        if len(selected) == 0:
            selected = self._imageGrid.images()

        if not self._allImagesAreProcessed(selected):
            # Show a dialog
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Some images are not processed yet. Please wait until all images are processed.")
            msg.setWindowTitle("Phantom is processing the images")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()
            return

        window = GroupFacesWindow(selected)
        self._childWindows.append(window)
        window.showMaximized()

    def _addImage(self, image_path: str) -> None:
        image = None
        try:
            image = Image(image_path)
        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")

        if image:
            self.project().images.append(image)
            self._imageGrid.addImage(image)
            self._itemsQueuedCount += 1
            ImageFeaturesService.instance().process(image)
            self._updateProgress()

    def _allImagesAreProcessed(self, images: list[Image]) -> bool:
        for image in images:
            if not image.processed:
                return False
        return True

    @QtCore.Slot(Image)
    def _onImageProcessed(self, image: Image) -> None:
        self._itemsProcessedCount += 1
        self._updateProgress()

    @QtCore.Slot(Image, Exception)
    def _onImageProcessingFailed(self, image: Image, error: Exception) -> None:
        self._itemsProcessedCount += 1
        self._updateProgress()
        print(f"Failed to process image {image.full_path}: {error}")

    def _updateProgress(self) -> None:
        items = self._itemsProcessedCount
        total = self._itemsQueuedCount if self._itemsQueuedCount > 0 else 1
        progress = items / total
        self._progressBar.setValue(progress * 100)

        if items == 0:
            self._progressBar.setVisible(False)
            pass
        elif items == total:
            self._progressBar.setVisible(False)
            self._itemsProcessedCount = 0
            self._itemsQueuedCount = 0
            self.statusBar().showMessage("All images are processed")
        else:
            self.statusBar().showMessage(f"Processing images... {items}/{total}")
            self._progressBar.setVisible(True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        for window in self._childWindows:
            window.close()

        event.accept()

    @QtCore.Slot()
    def _onOpenProjectPressed(self) -> None:
        file_path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select a project file", "", "Phantom Project (*.phantom)")

        if file_path:
            self._loadProject(file_path)

    @QtCore.Slot()
    def _onSaveProjectPressed(self) -> None:
        project = self.project()
        if project.file_path:
            self._saveProject(project.file_path)
        else:
            self._onSaveProjectAsPressed()

    @QtCore.Slot()
    def _onSaveProjectAsPressed(self) -> None:
        current_path = self.project().file_path
        file_dir = os.path.dirname(current_path) if current_path else ""

        file_path, _filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Select a project file", file_dir, "Phantom Project (*.phantom)")

        if file_path:
            if not file_path.endswith(".phantom"):
                file_path += ".phantom"

            self._saveProject(file_path)

    def _loadProject(self, file_path: str) -> None:
        reader = ProjectFileReader()
        project = reader.load(file_path)

        # close all child windows
        for window in self._childWindows:
            window.close()

        Application.instance().setCurrentProject(project)
        self._imageGrid.clear()
        for image in project.images:
            self._imageGrid.addImage(image)

    def _saveProject(self, file_path: str) -> None:
        project = ProjectFileWriter(minify=True)
        project.save(file_path, self.project())
