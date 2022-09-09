from PySide6 import QtGui, QtCore, QtWidgets
from src.Image import Image
from .PixmapDisplay import PixmapDisplay
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

class InspectorPanel(QtWidgets.QWidget):
    """
    A widget that displays a the properties of an image or a group of images.
    """
    def __init__(self):
        """
        Initializes the InspectorPanel class.
        """
        super().__init__()

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self.setContentsMargins(0, 0, 0, 0)

        # A 2 column table with "Property" and "Value" headers
        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Property", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self._table.verticalHeader().setDefaultSectionSize(20)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._table.setShowGrid(False)
        self._table.setContentsMargins(5, 5, 5, 5)


        self._layout.addWidget(self._table)

        self._pixmapDisplay = PixmapDisplay()
        self._pixmapDisplay.setMinimumHeight(200)
        self.setMinimumWidth(200)
        self._layout.addWidget(self._pixmapDisplay)
        
        self._selectedImages = []

    def setSelectedImages(self, images: list[Image]):
        """
        Sets the selected images.
        """
        self._selectedImages = images
        self._refresh_info()

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages

    def _get_exif(self, image: PILImage) -> dict[str, str]:
        """
        Gets the EXIF data from the image.
        """
        exif = {}
        info = image.getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif[decoded] = value

        return exif

    def _get_basic_info(self, image: PILImage) -> dict[str, str]:
        """
        Gets basic information about the image.
        """
        data = {
            "Filename": image.filename,
            "Image Width": image.width,
            "Image Height": image.height,
            "Image Format": image.format,
            "Color Channels": image.mode,
            "Animated": self._bool(getattr(image, "is_animated", False)),
        }
        frames = getattr(image, "n_frames", 1)
        if frames > 1:
            data["Number of Frames"] = frames
        
        return data

    def _bool(self, value: bool) -> str:
        """
        Converts a boolean value to a string.
        """
        return "Yes" if value else "No"

    def _refresh_info(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        # Clear the table
        self._table.setRowCount(0)

        selected_count = len(self._selectedImages)
        if selected_count == 0:
            self._pixmapDisplay.setPixmap(None)
        elif selected_count == 1:
            image = self._selectedImages[0]
            self._pixmapDisplay.setPixmap(image.pixmap)

            pil_image = PILImage.open(image.path)

            self._add_header("Basic Information")
            basic_info = self._get_basic_info(pil_image)
            for key, value in basic_info.items():
                self._add_row(key, value)

            self._add_header("EXIF Data")
            exif = self._get_exif(pil_image)
            if (len(exif) == 0):
                self._add_info("No EXIF data available.")
            else:
                for key, value in exif.items():
                    self._add_row(key, value)
        else:
            self._pixmapDisplay.setPixmap(None)
            label = str(selected_count) + " Images Selected"
            self._add_header(label)

    def _add_info(self, text: str):
        """
        Adds a header to the inspector panel.
        """
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setSpan(row, 0, 1, 2)
        self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(text))

    def _add_row(self, key: str, value: str):
        """
        Adds a row to the inspector panel.
        """
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
        self._table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(value)))

    def _add_header(self, text: str):
        """
        Adds a header to the inspector panel. 
        """
        header = InspectorHeader(text)
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setSpan(row, 0, 1, 2)
        self._table.setCellWidget(row, 0, header)
        

class InspectorHeader(QtWidgets.QWidget):
    """
    A header for the inspector panel. The header shows in bold text and has a blue line decoration that extends to the right.
    """
    def __init__(self, text: str):
        """
        Initializes the Header class.
        """
        super().__init__()

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(10, 0, 10, 0)
        self.setLayout(self._layout)

        self._label = QtWidgets.QLabel(text)
        self._label.setStyleSheet("font-weight: bold; color: #0b3e66; margin-right: 5px;")
        self._layout.addWidget(self._label)

        self._line = QtWidgets.QFrame()
        self._line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self._line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._line.setStyleSheet("color: #0078d7;")
        self._layout.addWidget(self._line)