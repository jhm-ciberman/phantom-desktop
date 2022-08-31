import sys
import os
import random
from PySide6.QtWidgets import (
    QApplication, QStyleFactory, QLabel, QPushButton, 
    QVBoxLayout, QWidget, QLineEdit, QCheckBox)

from PySide6.QtGui import QPalette, QPixmap, QImage
from PySide6.QtCore import Slot, Qt
from PySide6 import QtWidgets

import numpy as np
import cv2
from Image import Image

from phantom.utils import draw_faces
from phantom.faces import landmark

class ImageFrameDisplay(QLabel):
    """
    Widget for displaying an image. The image is scaled proportionally to fit the widget.

    Attributes:
        image (Image): The image to display.
    """
    def __init__(self, image = None, width = -1, height = -1):
        super().__init__()
        self._image = image
        self._pixmap = None
        self.setScaledContents(True)
        if image is not None:
            self.setImage(image)
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignCenter)
        

    def setImage(self, image):
        """
        Sets the image to display.
        """
        self._image = image
        qimage = QImage(image.raw_image.data, image.width, image.height, QImage.Format_RGBA8888)
        self._pixmap = QPixmap.fromImage(qimage)
        self._pixmap.scaled(self.size(), Qt.KeepAspectRatio)
        self.setPixmap(self._pixmap)
        self.update()


class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.hello_world_button = QPushButton("Click me!")
        self.cam_detect_demo_button = QPushButton("Open Cam detect demo")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text here")
        self.check_box = QCheckBox("Check me!")

        # load "../res/icon.png" as open cv image and then convert to QPixmap
        images = [
            "res/icon.png",
            "test_images/billboard.jpg"
        ]

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.hello_world_button)
        self.layout.addWidget(self.cam_detect_demo_button)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.check_box)

        for image_path in images:
            image = Image.from_path(image_path)
            image_frame_display = ImageFrameDisplay(image)
            image_frame_display.setFixedSize(200, 200)
            self.layout.addWidget(image_frame_display)
        
        self.setLayout(self.layout)

        # Connecting the signal
        self.hello_world_button.clicked.connect(self.magic)
        self.cam_detect_demo_button.clicked.connect(self.open_cam_detect_demo)

    @Slot()
    def magic(self) -> None:
        self.text.setText(random.choice(self.hello))

    @Slot()
    def open_cam_detect_demo(self) -> None:
        video = cv2.VideoCapture(0)

        while True:
            check, frame = video.read()
            faces = landmark(frame, upsample=1)
            frame = draw_faces(frame, faces)
            cv2.imshow("Caras", frame)
            key = cv2.waitKey(1)
            if key == ord("q"):
                break

        video.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    for style in QStyleFactory.keys():
        print(style)

    app.style = QStyleFactory.create("Fusion")
    #app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    p = app.palette()
    p.setColor(QPalette.Window, Qt.white)
    app.setPalette(p)

    # app.setStyle(QStyleFactory.create("Fusion"))
    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())
