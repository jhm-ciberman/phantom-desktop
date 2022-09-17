from PySide6 import QtGui, QtCore, QtWidgets
from src.Image import Image


class ImageGrid(QtWidgets.QWidget):
    """
    A widget that displays a grid of images.
    """

    selectionChanged = QtCore.Signal()

    def __init__(self):
        """
        Initializes the ImageGrid class.
        """
        super().__init__()
        self._images = []
        self._items = []
        self._selectedImages = []
        self._gridSize = QtCore.QSize(150, 150)
        self._iconSize = QtCore.QSize(130, 100)
        self._listWidget = QtWidgets.QListWidget()
        self._listWidget.setContentsMargins(0, 0, 0, 0)
        self._listWidget.setGridSize(self._gridSize)
        self._listWidget.setIconSize(self._iconSize)
        self._listWidget.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self._listWidget.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self._listWidget.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self._listWidget.setMovement(QtWidgets.QListView.Movement.Static)
        self._listWidget.setDragDropMode(QtWidgets.QListView.DragDropMode.NoDragDrop)
        self._listWidget.setSelectionMode(QtWidgets.QListView.SelectionMode.ExtendedSelection)
        self._listWidget.setSelectionBehavior(QtWidgets.QListView.SelectionBehavior.SelectItems)
        self._listWidget.setItemDelegate(_TextOverDelegate(self))

        self._loadingIcon = QtGui.QIcon("res/loading.png")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._listWidget)
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)

        self._listWidget.itemSelectionChanged.connect(self._onItemSelectionChanged)

    def addImage(self, image: Image) -> None:
        """
        Adds an image to the grid.

        Args:
            image (Image): The image to add.
        """
        qimage = QtGui.QImage(image.raw_image.data, image.width, image.height, QtGui.QImage.Format_RGBA8888)
        pixmap = QtGui.QPixmap.fromImage(qimage)
        item = QtWidgets.QListWidgetItem(pixmap, image.basename, self._listWidget)
        item.setSizeHint(self._gridSize)
        self._items.append(item)
        self._images.append(image)
        self._items.append(item)

    def removeImage(self, index: int) -> None:
        """
        Removes an image from the grid.
        """
        self._listWidget.takeItem(index)
        self._images.pop(index)
        self._items.pop(index)

    def images(self) -> list[Image]:
        """
        Gets the images in the grid.
        """
        return self._images

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images in the grid.
        """
        return self._selectedImages

    def _onItemSelectionChanged(self) -> None:
        self._selectedImages = []
        for item in self._listWidget.selectedIndexes():
            self._selectedImages.append(self._images[item.row()])

        self.selectionChanged.emit()

    def clear(self) -> None:
        """
        Clears the grid.
        """
        self._listWidget.clear()
        self._images = []
        self._items = []
        self._selectedImages = []


class _TextOverDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, imageGrid: ImageGrid, parent=None):
        self._imageGrid = imageGrid
        super().__init__(parent)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        itemIndex = index.row()
        image = self._imageGrid.images()[itemIndex]
        if not image.processed:
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            # draw loading icon
            iconRect = QtCore.QRect(option.rect.x() + 5, option.rect.y() + 5, 24, 24)
            self._imageGrid._loadingIcon.paint(painter, iconRect)
            painter.restore()
