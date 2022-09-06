from PySide6 import QtGui, QtCore, QtWidgets

from .QtHelpers import setSplitterStyle
from .Widgets.ImageGrid import ImageGrid
from .Widgets.InspectorPanel import InspectorPanel
from .Image import Image
from .PerspectiveWindow import PerspectiveWindow
from phantom.utils import draw_faces
from phantom.faces import landmark
import cv2
import glob
import os

class MainWindow(QtWidgets.QMainWindow):
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

        self.cam_detect_demo_button = QtWidgets.QPushButton("Open Cam detect demo")
        self.cam_detect_demo_button.clicked.connect(self.open_cam_detect_demo)
        self._layout.addWidget(self.cam_detect_demo_button, 0, QtCore.Qt.AlignTop)

        self.perspective_correct_button = QtWidgets.QPushButton("Open Perspective Correct Window")
        self.perspective_correct_button.clicked.connect(self.open_perspective_correct_window)
        self._layout.addWidget(self.perspective_correct_button, 0, QtCore.Qt.AlignTop)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        splitter.setContentsMargins(10, 10, 10, 10)
        setSplitterStyle(splitter)

        self.image_grid = ImageGrid()
        for image_path in self.get_test_image_paths():
            try:
                image = Image(image_path)
                self.image_grid.addImage(image)
            except Exception as e:
                print(f"Failed to load image {image_path}: {e}")
        
        self.image_grid.selectionChanged.connect(self.on_image_grid_selection_changed)

        self.inspector_panel = InspectorPanel()
        self.inspector_panel.setContentsMargins(0, 0, 0, 0)
        
        splitter.addWidget(self.image_grid)
        splitter.addWidget(self.inspector_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        self._layout.addWidget(splitter, 1)
        mainWidget.setLayout(self._layout)
        self.setCentralWidget(mainWidget)

        self._menuBar = self.menuBar()
        self._fileMenu = self._menuBar.addMenu("&File")
        self._fileMenu.addAction("&Import image", self.import_image)
        self._fileMenu.addAction("&Export image", self.export_image)
        self._fileMenu.addAction("&Exit", self.close)

        self._childWindows = [] # Only because GC closes the window when the reference is lost.

    def get_test_image_paths(self):
        max_image_count = 2000
        image_paths = [
            "test_images/icon.png",
            "test_images/billboard.jpg",
            "test_images/cookies-800x400.jpg",
        ]
        image_paths += glob.glob("test_images/exif/**/*.jpg", recursive=True)
        image_paths += glob.glob("test_images/exif/**/*.tiff", recursive=True)
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
            self.statusBar().showMessage("{} images in the collection".format(len(self.image_grid.images())))
        elif (count == 1):
            self.statusBar().showMessage(selected_images[0].path)
        else:
            self.statusBar().showMessage("{} images selected".format(count))

    @QtCore.Slot()
    def import_image(self) -> None:
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "Images (*.png *.jpg *.jpeg)")[0]
        if file_path:
            image = Image(file_path)
            self.image_grid.addImage(image)

    @QtCore.Slot()
    def export_image(self) -> None:
        selected_images = self.image_grid.selectedImages()
        if len(selected_images) == 1:
            file_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "Images (*.png *.jpg *.jpeg)")[0]
            if file_path:
                selected_images[0].save(file_path)

    @QtCore.Slot()
    def open_perspective_correct_window(self) -> None:
        selected = self.image_grid.selectedImages()
        if len(selected) == 1:
            window = PerspectiveWindow(selected[0])
            self._childWindows.append(window)
            window.showMaximized()

            print("Opening perspective correct window")