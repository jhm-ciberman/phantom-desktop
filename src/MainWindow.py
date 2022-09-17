from PySide6 import QtGui, QtCore, QtWidgets

from .Services.LoadingWorker import LoadingWorker

from .QtHelpers import setSplitterStyle
from .Widgets.ImageGrid import ImageGrid
from .Widgets.InspectorPanel import InspectorPanel
from .Image import Image
from .PerspectiveWindow import PerspectiveWindow
from .DeblurWindow import DeblurWindow
from .GroupFacesWindow import GroupFacesWindow
import glob


class MainWindow(QtWidgets.QMainWindow):

    onLoaded = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Phantom")
        self.setMinimumSize(800, 600)

        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().setFixedHeight(20)
        self.statusBar().showMessage("Phantom Desktop")

        mainWidget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._addImagesAction = QtGui.QAction(
            QtGui.QIcon("res/image_add.png"), "Add Images", self)
        self._addImagesAction.setToolTip("Add images to current project")
        self._addImagesAction.triggered.connect(self.onAddImagesPressed)

        self._exportImageAction = QtGui.QAction(
            QtGui.QIcon("res/image_save.png"), "Export Image", self)
        self._exportImageAction.triggered.connect(self.onExportImagePressed)

        self._correctPerspectiveAction = QtGui.QAction(
            QtGui.QIcon("res/correct_perspective.png"), "Correct Perspective", self)
        self._correctPerspectiveAction.triggered.connect(self.onCorrectPerspectivePressed)

        self._deblurAction = QtGui.QAction(
            QtGui.QIcon("res/deblur.png"), "Deblur Filter", self)
        self._deblurAction.triggered.connect(self.onDeblurPressed)

        self._groupFacesAction = QtGui.QAction(
            QtGui.QIcon("res/group_faces.png"), "Group Similar Faces", self)
        self._groupFacesAction.triggered.connect(self.onGroupFacesPressed)

        self._exitAction = QtGui.QAction(
            QtGui.QIcon("res/exit.png"), "Exit", self)
        self._exitAction.triggered.connect(self.close)

        self._toolbar = QtWidgets.QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self._toolbar.setIconSize(QtCore.QSize(48, 48))
        self._toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toolbar.addAction(self._addImagesAction)
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

        self.imageGrid = ImageGrid()
        for image_path in self.getTestImagePaths():
            self._addImage(image_path)

        self.imageGrid.selectionChanged.connect(self.onImageGridSelectionChanged)

        self.inspector_panel = InspectorPanel()
        self.inspector_panel.setContentsMargins(0, 0, 0, 0)

        splitter.addWidget(self.imageGrid)
        splitter.addWidget(self.inspector_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        self._layout.addWidget(splitter, 1)
        mainWidget.setLayout(self._layout)
        self.setCentralWidget(mainWidget)

        self._menuBar = self.menuBar()
        self._fileMenu = self._menuBar.addMenu("&File")
        self._fileMenu.addAction(self._addImagesAction)
        self._fileMenu.addAction(self._exportImageAction)
        self._fileMenu.addAction(self._exitAction)

        self._editMenu = self._menuBar.addMenu("&Edit")
        self._editMenu.addAction(self._correctPerspectiveAction)
        self._editMenu.addAction(self._deblurAction)
        self._editMenu.addAction(self._groupFacesAction)

        self._childWindows = []  # Only because GC closes the window when the reference is lost.

        self.onImageGridSelectionChanged()  # Refresh the UI for the first time.

        LoadingWorker.instance().on_image_processed.connect(self.onWorkerImageProcessed)
        LoadingWorker.instance().start()

    def getTestImagePaths(self):
        max_image_count = 2000
        image_paths = [
            "test_images/icon.png",
            "test_images/billboard.jpg",
            "test_images/cookies-800x400.jpg",
            "test_images/lena.png",
            "test_images/lena_blur_3.png",
            "test_images/lena_blur_10.png",
        ]
        image_paths += glob.glob("test_images/exif/**/*.jpg", recursive=True)
        image_paths += glob.glob("test_images/exif/**/*.tiff", recursive=True)
        image_paths += glob.glob("test_images/celebrities/**/*.jpg", recursive=True)

        return image_paths[:max_image_count]

    @QtCore.Slot()
    def onImageGridSelectionChanged(self) -> None:
        selected_images = self.imageGrid.selectedImages()
        self.inspector_panel.setSelectedImages(selected_images)
        count = len(selected_images)
        if (count == 0):
            self.statusBar().showMessage("{} images in the collection".format(len(self.imageGrid.images())))
        elif (count == 1):
            self.statusBar().showMessage(selected_images[0].path)
        else:
            self.statusBar().showMessage("{} images selected".format(count))

        self._exportImageAction.setEnabled(count > 0)
        self._correctPerspectiveAction.setEnabled(count == 1)
        self._deblurAction.setEnabled(count == 1)
        self._groupFacesAction.setEnabled(count > 1 or count == 0)

    @QtCore.Slot()
    def onAddImagesPressed(self) -> None:
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "Images (*.png *.jpg *.jpeg)")[0]
        if file_path:
            self._addImage(file_path)

    @QtCore.Slot()
    def onExportImagePressed(self) -> None:
        selected_images = self.imageGrid.selectedImages()
        if len(selected_images) == 1:
            file_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "Images (*.png *.jpg *.jpeg)")[0]
            if file_path:
                selected_images[0].save(file_path)

    @QtCore.Slot()
    def onCorrectPerspectivePressed(self) -> None:
        selected = self.imageGrid.selectedImages()
        if len(selected) == 1:
            window = PerspectiveWindow(selected[0])
            self._childWindows.append(window)
            window.showMaximized()

    @QtCore.Slot()
    def onDeblurPressed(self) -> None:
        selected = self.imageGrid.selectedImages()
        if len(selected) == 1:
            window = DeblurWindow(selected[0])
            self._childWindows.append(window)
            window.showMaximized()

    @QtCore.Slot()
    def onGroupFacesPressed(self) -> None:
        selected = self.imageGrid.selectedImages()
        if len(selected) == 1:
            return

        if len(selected) == 0:
            selected = self.imageGrid.images()

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
        try:
            image = Image(image_path)
            self.imageGrid.addImage(image)
            LoadingWorker.instance().add_image(image)
        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")

    def _allImagesAreProcessed(self, images: list[Image]) -> bool:
        for image in images:
            if not image.processed:
                return False
        return True

    @QtCore.Slot(Image)
    def onWorkerImageProcessed(self, image: Image) -> None:
        self.imageGrid.repaint()
