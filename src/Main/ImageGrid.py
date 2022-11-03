from PySide6 import QtCore, QtGui, QtWidgets

from ..Application import Application
from ..l10n import __
from ..Models import Image
from ..Widgets.GridBase import GridBase


class ImageGrid(GridBase):
    """
    A widget that displays a grid of images.
    """

    imageSelectionChanged = QtCore.Signal()
    """Raised when the selected image changes."""

    deblurImagePressed = QtCore.Signal(Image)
    """Raised when the "Deblur Filter" right-click action is invoked."""

    perspectivePressed = QtCore.Signal(Image)
    """Raised when the "Correct perspective" right-click action is invoked."""

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

        self._loadingIcon = QtGui.QIcon("res/img/loading.png")
        self._faceIcon = QtGui.QIcon("res/img/person.png")

        self.itemSelectionChanged.connect(self._onItemSelectionChanged)
        Application.workspace().imageProcessed.connect(self._onImageProcessed)

        def onPressed(sinal: QtCore.Signal):
            image = self._images[self.selectedIndexes()[0].row()]
            sinal.emit(image)

        # Right-click actions for when a user right-clicks on the image.
        self._menu = QtWidgets.QMenu()

        self._perspectiveAction = self._menu.addAction(
            QtGui.QIcon("res/img/correct_perspective.png"),
            __("Correct perspective"),
            lambda: onPressed(self.perspectivePressed))

        self._deblurAction = self._menu.addAction(
            QtGui.QIcon("res/img/deblur.png"),
            __("Deblur Filter"),
            lambda: onPressed(self.deblurImagePressed))

        self._menu.addSeparator()

        self._openInExternalImageViewerAction = self._menu.addAction(
            QtGui.QIcon("res/img/photo_viewer.png"),
            __("Open In External Image Viewer"),
            self._onOpenInExternalImageViewer)

        self._openInExplorerAction = self._menu.addAction(
            QtGui.QIcon("res/img/folder.png"),
            __("Open In Explorer"),
            self._onOpenInExplorer)

        self._menu.addSeparator()

        self._exportImagesAction = self._menu.addAction(
            QtGui.QIcon("res/img/image_save.png"),
            __("Export Image"),
            self._onExportImage)

        self._removeFromProjectAction = self._menu.addAction(
            QtGui.QIcon("res/img/times.png"),
            __("Remove from Project"),
            self._onRemoveFromProject)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Handles the context menu event.
        """
        count = len(self.selectedIndexes())
        if count > 0:
            self._openInExternalImageViewerAction.setEnabled(count == 1)
            self._openInExplorerAction.setEnabled(count == 1)
            self._deblurAction.setEnabled(count == 1)
            self._perspectiveAction.setEnabled(count == 1)
            self._exportImagesAction.setEnabled(count > 0)
            self._exportImagesAction.setText(__("Export Image") if count == 1 else __("Export Images"))
            self._removeFromProjectAction.setEnabled(count > 0)
            self._menu.exec_(event.globalPos())

    def addImage(self, image: Image) -> None:
        """
        Adds an image to the grid.

        Args:
            image (Image): The image to add.
        """
        pixmap = image.get_pixmap()
        self.addItemCore(pixmap, image.display_name)
        self._images.append(image)

    def removeImage(self, image: Image) -> None:
        """
        Removes an image from the grid.
        """
        if image in self._selectedImages:
            self._selectedImages.remove(image)
        index = self._images.index(image)
        if index < 0:
            return
        self._images.remove(image)
        self.takeItem(index)

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
            i = item.row()
            if i < len(self._images):
                self._selectedImages.append(self._images[i])

        self.imageSelectionChanged.emit()

    def clear(self) -> None:
        """
        Clears the grid.
        """
        self._images = []
        self._selectedImages = []
        super().clear()
        self.imageSelectionChanged.emit()

    @QtCore.Slot(Image)
    def _onImageProcessed(self, image: Image) -> None:
        """
        Updates the grid when an image is processed.
        """
        if image not in self._images:
            return
        index = self._images.index(image)
        self.update(self.model().index(index, 0))

    @QtCore.Slot()
    def _onOpenInExternalImageViewer(self) -> None:
        """
        Opens the selected image in the default image viewer.
        """
        indexes = self.selectedIndexes()
        if len(indexes) != 1:
            return
        image = self._images[indexes[0].row()]
        Application.projectManager().openImageExternally(image)

    @QtCore.Slot()
    def _onOpenInExplorer(self) -> None:
        """
        Opens the selected image in the default file explorer.
        """
        indexes = self.selectedIndexes()
        if len(indexes) != 1:
            return
        image = self._images[indexes[0].row()]
        Application.projectManager().openImageInExplorer(image)

    @QtCore.Slot()
    def _onRemoveFromProject(self) -> None:
        """
        Removes the selected image from the project.
        """
        Application.workspace().removeImages(self.selectedImages())

    @QtCore.Slot()
    def _onExportImage(self) -> None:
        selectedImages = self.selectedImages()
        Application.projectManager().exportImages(self, selectedImages)


class _TextOverDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, imageGrid: ImageGrid, parent=None):
        self._imageGrid = imageGrid
        super().__init__(parent)

    def _getIcon(self, image: Image):
        if not image._processed:
            return self._imageGrid._loadingIcon
        elif len(image.faces) > 0:
            return self._imageGrid._faceIcon
        else:
            return None

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        itemIndex = index.row()
        images = self._imageGrid.images()
        if itemIndex >= len(images):
            return
        image = images[itemIndex]
        icon = self._getIcon(image)

        if icon is not None:
            painter.save()
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            # draw loading icon
            iconRect = QtCore.QRect(option.rect.x() + 2, option.rect.y() + 2, 24, 24)
            icon.paint(painter, iconRect)
            painter.restore()
