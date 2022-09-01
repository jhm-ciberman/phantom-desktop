from PySide6 import QtGui, QtCore, QtWidgets
from Widgets.PixmapDisplay import PixmapDisplay
from Image import Image

class ImageGrid(QtWidgets.QWidget):
    """
    A widget that displays a grid of images.
    """
    def __init__(self):
        """
        Initializes the ImageGrid class.
        """
        super().__init__()
        self._images = []
        self._imageDisplayWidgets = []
        self._columnsCount = 4
        self._rowHeight = 150
        self._layout = QtWidgets.QGridLayout()
        self.setLayout(self._layout)
    
    def addImage(self, image: Image) -> None:
        """
        Adds an image to the grid.

        Args:
            image (Image): The image to add.
        """
        qimage = QtGui.QImage(image.raw_image.data, image.width, image.height, QtGui.QImage.Format_RGBA8888)
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self._images.append(image)
        item = ImageGridItem(pixmap, image.basename)
        item.setFixedHeight(self._rowHeight)
        self._imageDisplayWidgets.append(item)
        self._addWidget(item, len(self._imageDisplayWidgets) - 1)

    def removeImage(self, index: int) -> None:
        """
        Removes an image from the grid.
        """
        self._layout.itemAt(index).widget().setParent(None)
        self._images.pop(index)
        self._imageDisplayWidgets.pop(index)
        self._updateLayout()

    def clear(self) -> None:
        """
        Clears the grid.
        """
        self._images = []
        self._imageDisplayWidgets = []
        self._updateLayout()

    def images(self) -> list:
        """
        Gets the images in the grid.
        """
        return self._images    

    def setColumnsCount(self, columnsCount: int) -> None:
        """
        Sets the number of columns in the grid.
        """
        self._columnsCount = columnsCount
        self._updateLayout()

    def columnsCount(self) -> int:
        """
        Gets the number of columns in the grid.
        """
        return self._columnsCount

    def _updateLayout(self) -> None:
        # Remove all widgets from the layout.
        for i in reversed(range(self._layout.count())):
            self._layout.itemAt(i).widget().setParent(None)

        # Re-add the widgets to the layout.
        for i in range(len(self._imageDisplayWidgets)):
            self._addWidget(self._imageDisplayWidgets[i], i)
        
    def _addWidget(self, widget: QtWidgets.QWidget, index: int) -> None:
        row = index // self._columnsCount
        column = index % self._columnsCount
        self._layout.addWidget(widget, row, column)

    def setRowHeight(self, rowHeight: int) -> None:
        """
        Sets the height of each row in the grid.
        """
        self._rowHeight = rowHeight
        for i in range(len(self._imageDisplayWidgets)):
            self._imageDisplayWidgets[i].setFixedHeight(rowHeight)

    def rowHeight(self) -> int:
        """
        Gets the height of each row in the grid.
        """
        return self._rowHeight



class ImageGridItem(QtWidgets.QWidget):
    """
    Displays a QPixmap with a label below. This widget is used in the ImageGrid class.
    """
    def __init__(self, pixmap: QtGui.QPixmap = None, label = None):
        """
        Initializes the ImageThumbnail class.

        Args:
            pixmap (QPixmap): The pixmap to display.
            label (str): The label to display.
        """
        super().__init__()
        self._pixmapDisplayWidget = PixmapDisplay(pixmap)
        self._labelWidget = QtWidgets.QLabel(label)
        self._labelWidget.setAlignment(QtCore.Qt.AlignCenter)
        self._labelWidget.setStyleSheet("QLabel { font-size: 12px; }")
        self._labelWidget.setFixedHeight(20)
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addWidget(self._pixmapDisplayWidget)
        self._layout.addWidget(self._labelWidget)
        self.setLayout(self._layout)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setContentsMargins(0, 0, 0, 0)
        
    def setPixmap(self, pixmap: QtGui.QPixmap) -> None:
        """
        Sets the pixmap to display.

        Args:
            pixmap (QPixmap): The pixmap to display.
        """
        self._pixmapDisplayWidget.setPixmap(pixmap)

    def pixmap(self) -> QtGui.QPixmap:
        """
        Gets the pixmap to display.
        """
        return self._pixmapDisplayWidget.pixmap()

    def setTransformationMode(self, transformationMode: QtCore.Qt.TransformationMode) -> None:
        """
        Sets the transformation mode to use when scaling the image.
        """
        self._pixmapDisplayWidget.setTransformationMode(transformationMode)

    def transformationMode(self) -> QtCore.Qt.TransformationMode:
        """
        Gets the transformation mode to use when scaling the image.
        """
        return self._pixmapDisplayWidget.transformationMode()

    def setLabel(self, label: str) -> None:
        """
        Sets the label to display.
        """
        self._labelWidget.setText(label)

    def label(self) -> str:
        """
        Gets the label to display.
        """
        return self._labelWidget.text()
        