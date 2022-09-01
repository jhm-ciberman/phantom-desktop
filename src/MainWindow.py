from PySide6 import QtGui, QtCore, QtWidgets
from Widgets.ImageGrid import ImageGrid
from Image import Image
from phantom.utils import draw_faces
from phantom.faces import landmark
import cv2
import glob

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        icon = QtGui.QIcon("res/icon_128.png")
        self.setWindowIcon(icon)
        self.setWindowTitle("Phantom")

        self.layout = QtWidgets.QVBoxLayout()

        self.cam_detect_demo_button = QtWidgets.QPushButton("Open Cam detect demo")
        self.cam_detect_demo_button.clicked.connect(self.open_cam_detect_demo)
        self.layout.addWidget(self.cam_detect_demo_button)



        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.image_grid = ImageGrid()
        for image_path in self.get_test_image_paths():
            image = Image.from_path(image_path)
            self.image_grid.addImage(image)
        
        self.image_grid.selectionChanged.connect(self.on_image_grid_selection_changed)

        self.setLayout(self.layout)
        self.layout.addWidget(scroll_area)
        scroll_area.setWidget(self.image_grid)

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
        print("Selection changed")
        for item in self.image_grid.selectedImages():
            print(item.path)
