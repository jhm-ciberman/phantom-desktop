import sys
import random
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton,
                               QVBoxLayout, QWidget)
from PySide6.QtCore import Slot, Qt

import numpy as np
import cv2

from phantom.utils import draw_faces
from phantom.faces import landmark

class MyWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.hello = ["Hallo Welt", "你好，世界", "Hei maailma",
            "Hola Mundo", "Привет мир"]

        self.hello_world_button = QPushButton("Click me!")
        self.cam_detect_demo_button = QPushButton("Open Cam detect demo")

        self.text = QLabel("Hello World")
        self.text.setAlignment(Qt.AlignCenter)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.hello_world_button)
        self.layout.addWidget(self.cam_detect_demo_button)
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
    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())
