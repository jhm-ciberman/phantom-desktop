from PySide6 import QtGui, QtCore, QtWidgets
from src.Image import Image
from .GridBase import GridBase


class ImageGrid(GridBase):
    """
    A widget that displays a grid of images.
    """

    selectionChanged = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initializes a new instance of the ImageGrid class.
        """
        super().__init__(parent)
        self._images = []
        self._selectedImages = []
        # self.setGridSize(QtCore.QSize(150, 150))
        # self.setIconSize(QtCore.QSize(130, 100))
        self.setSelectionMode(QtWidgets.QListView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QListView.SelectionBehavior.SelectItems)
        self.setItemDelegate(_TextOverDelegate(self))

        self._loadingIcon = QtGui.QIcon("res/loading.png")
        self._faceIcon = QtGui.QIcon("res/person.png")

        self.itemSelectionChanged.connect(self._onItemSelectionChanged)

    def addImage(self, image: Image) -> None:
        """
        Adds an image to the grid.

        Args:
            image (Image): The image to add.
        """
        pixmap = image.get_pixmap()
        self._addItemCore(pixmap, image.basename)
        self._images.append(image)

    def removeImage(self, index: int) -> None:
        """
        Removes an image from the grid.
        """
        self.takeItem(index)
        self._images.pop(index)

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
        for item in self.selectedIndexes():
            self._selectedImages.append(self._images[item.row()])

        self.selectionChanged.emit()

    def clear(self) -> None:
        """
        Clears the grid.
        """
        self._images = []
        self._selectedImages = []
        super().clear()
        self.selectionChanged.emit()


class _TextOverDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, imageGrid: ImageGrid, parent=None):
        self._imageGrid = imageGrid
        super().__init__(parent)

    def _getIcon(self, image: Image):
        if not image.processed:
            return self._imageGrid._loadingIcon
        elif len(image.faces) > 0:
            return self._imageGrid._faceIcon
        else:
            return None

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        itemIndex = index.row()
        image = self._imageGrid.images()[itemIndex]
        icon = self._getIcon(image)

        if icon is not None:
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            # draw loading icon
            iconRect = QtCore.QRect(option.rect.x() + 2, option.rect.y() + 2, 24, 24)
            icon.paint(painter, iconRect)
            painter.restore()
