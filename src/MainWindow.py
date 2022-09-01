from PySide6 import QtGui, QtCore, QtWidgets
from Widgets.ImageGrid import ImageGrid
from Widgets.InspectorPanel import InspectorPanel
from Image import Image
from phantom.utils import draw_faces
from phantom.faces import landmark
import cv2
import glob
import os

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        icon = QtGui.QIcon("res/icon_128.png")
        self.setWindowIcon(icon)
        self.setWindowTitle("Phantom")

        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().setFixedHeight(20)
        self.statusBar().showMessage("Hola como estás wei")


        self.cam_detect_demo_button = QtWidgets.QPushButton("Open Cam detect demo")
        self.cam_detect_demo_button.clicked.connect(self.open_cam_detect_demo)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.splitter.setContentsMargins(10, 10, 10, 10)
        # The splitter is invisible due to a bug in Qt so we use an image instead.
        self.splitter.setStyleSheet("QSplitter::handle { image: url(res/drag_handle_horizontal.png); }")

        self.image_grid = ImageGrid()
        for image_path in self.get_test_image_paths():
            image = Image.from_path(image_path)
            self.image_grid.addImage(image)
        
        self.image_grid.selectionChanged.connect(self.on_image_grid_selection_changed)

        self.inspector_panel = InspectorPanel()
        self.inspector_panel.setContentsMargins(0, 0, 0, 0)
        
        self.splitter.addWidget(self.image_grid)
        self.splitter.addWidget(self.inspector_panel)
        self.splitter.setStretchFactor(0, 1)

        self._mainWidget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.cam_detect_demo_button, 0, QtCore.Qt.AlignTop)
        self._layout.addWidget(self.splitter, 1)
        self._mainWidget.setLayout(self._layout)
        self.setCentralWidget(self._mainWidget)

        self._menuBar = self.menuBar()
        self._fileMenu = self._menuBar.addMenu("&File")
        self._fileMenu.addAction("&Import image", self.import_image)
        self._fileMenu.addAction("&Export image", self.export_image)
        self._fileMenu.addAction("&Exit", self.close)

    def get_test_image_paths(self):
        max_image_count = 1000
        image_paths = [
            "test_images/icon.png",
            "test_images/billboard.jpg",
            "test_images/cookies-800x400.jpg",
        ]
        image_paths += glob.glob("test_images/celebrities/**/*.jpg", recursive=True)
        
        return image_paths[:max_image_count]

    @QtCore.Slot()
    def open_cam_detect_demo(self) -> None:
        video = cv2.VideoCapture(0)

        while True:
            _, frame = video.read()
            faces = landmark(frame, upsample=1)
            frame = draw_faces(frame, faces)
            cv2.imshow("Caras", frame)
            key = cv2.waitKey(1)
            if key == ord("q"):
                break

        video.release()

    @QtCore.Slot()
    def on_image_grid_selection_changed(self) -> None:
        selected_images = self.image_grid.selectedImages()
        self.inspector_panel.setSelectedImages(selected_images)
        count = len(selected_images)
        if (count == 0):
            self.statusBar().showMessage("{} images in the collection".format(self.image_grid.images().count()))
        elif (count == 1):
            self.statusBar().showMessage(selected_images[0].path)
        else:
            self.statusBar().showMessage("{} images selected".format(count))

    @QtCore.Slot()
    def import_image(self) -> None:
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "Images (*.png *.jpg *.jpeg)")[0]
        if file_path:
            image = Image.from_path(file_path)
            self.image_grid.addImage(image)

    @QtCore.Slot()
    def export_image(self) -> None:
        selected_images = self.image_grid.selectedImages()
        if len(selected_images) == 1:
            file_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "Images (*.png *.jpg *.jpeg)")[0]
            if file_path:
                selected_images[0].save(file_path)