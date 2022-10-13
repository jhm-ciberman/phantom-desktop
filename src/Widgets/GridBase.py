from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from src.l10n import __


class SizePreset:
    """
    Represents a size preset for a grid.
    """
    def __init__(self, name: str, gridSize: QtCore.QSize, iconSize: QtCore.QSize) -> None:
        """
        Initializes a new instance of the SizePreset class.

        Args:
            name (str): The name of the preset.
            gridSize (QSize): The size of the grid.
            iconSize (QSize): The size of the icons.
        """
        self.name = name
        self.gridSize = gridSize
        self.iconSize = iconSize


class GridBase(QtWidgets.QListWidget):
    """
    A Widget class that provides base functionality to show a grid of images.
    The methods addItemCore and setItemCore can be used to easily add items to
    the grid. This class can be used by itself or as a base class to provide advanced
    functionality.
    """

    class _ItemData:
        def __init__(self, pixmap: QtGui.QPixmap, text: str) -> None:
            self.pixmap = pixmap
            self.text = text

    smallPreset = SizePreset(__("@grid_presets.small"), QtCore.QSize(100, 100), QtCore.QSize(80, 80))

    mediumPreset = SizePreset(__("@grid_presets.medium"), QtCore.QSize(150, 150), QtCore.QSize(120, 120))

    largePreset = SizePreset(__("@grid_presets.large"), QtCore.QSize(200, 200), QtCore.QSize(160, 160))

    hugePreset = SizePreset(__("@grid_presets.huge"), QtCore.QSize(250, 250), QtCore.QSize(200, 200))

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the GridBase class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        self._itemsSources = []  # type: list[GridBase._ItemData]
        self._sizePreset = None  # type: SizePreset

        self.setContentsMargins(0, 0, 0, 0)
        self.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.setMovement(QtWidgets.QListView.Movement.Static)
        self.setDragDropMode(QtWidgets.QListView.DragDropMode.NoDragDrop)
        self.setSelectionMode(QtWidgets.QListView.SelectionMode.SingleSelection)
        self.setSizePreset(GridBase.mediumPreset)

    def addItemCore(self, pixmap: QtGui.QPixmap, text: str, data: Any = None) -> None:
        """
        Add an item to the list.

        Args:
            pixmap (QPixmap): The pixmap to display.
            text (str): The text to display.
            data (Any): The data to associate with the item.
        """
        item = QtWidgets.QListWidgetItem()
        self.setItemCore(item, pixmap, text, data)

        self.addItem(item)
        self._itemsSources.append(GridBase._ItemData(pixmap, text))

    def setItemCore(self, item: QtWidgets.QListWidgetItem, pixmap: QtGui.QPixmap, text: str, data: Any = None) -> None:
        """
        Updates the item with the given pixmap and text.

        Args:
            item (QListWidgetItem): The item to update.
            pixmap (QPixmap): The pixmap to display.
            text (str): The text to display.
            data (Any): The data to associate with the item.
        """
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom)
        item.setSizeHint(self.gridSize())
        resizedPixmap = pixmap.scaled(self.iconSize(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        item.setIcon(QtGui.QIcon(resizedPixmap))
        item.setText(text)
        item.setToolTip(text)
        item.setStatusTip(text)

        if data is not None:
            item.setData(QtCore.Qt.ItemDataRole.UserRole, data)

    def getItemData(self, index: int) -> Any:
        """
        Gets the data associated with the item at the given index.

        Args:
            index (int): The index of the item.

        Returns:
            Any: The data associated with the item.
        """
        return self.item(index).data(QtCore.Qt.ItemDataRole.UserRole)

    def clear(self) -> None:
        """
        Clear the grid.
        """
        self._itemsSources.clear()
        super().clear()

    def _resizeItems(self) -> None:
        """
        Resize the items to fit the current icon size.
        """
        for i, item in enumerate(self._itemsSources):
            resizedPixmap = item.pixmap.scaled(self.iconSize(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self.item(i).setIcon(QtGui.QIcon(resizedPixmap))

    def setIconSize(self, size: QtCore.QSize) -> None:
        """
        Set the icon size.

        Args:
            size (QSize): The icon size.
        """
        super().setIconSize(size)
        self._resizeItems()

    def setSizePreset(self, sizePreset: SizePreset) -> None:
        """
        Set the size preset.

        Args:
            sizePreset (SizePreset): The size preset.
        """
        self._sizePreset = sizePreset
        self.setGridSize(sizePreset.gridSize)
        self.setIconSize(sizePreset.iconSize)

    @staticmethod
    def sizePresets() -> list[SizePreset]:
        """
        Get the available size presets.

        Returns:
            list[SizePreset]: The available size presets.
        """
        return [GridBase.smallPreset, GridBase.mediumPreset, GridBase.largePreset, GridBase.hugePreset]

    def sizePreset(self) -> SizePreset:
        """
        Get the current size preset.

        Returns:
            SizePreset: The current size preset.
        """
        return self._sizePreset

    def setGridSize(self, size: QtCore.QSize) -> None:
        """
        Set the grid size.

        Args:
            size (QSize): The grid size.
        """
        super().setGridSize(size)

        for i in range(self.count()):
            self.item(i).setSizeHint(size)
