from PySide6 import QtCore, QtWidgets
from .Image import Image


class GroupFacesWindow(QtWidgets.QWidget):
    def __init__(self, images: list[Image]) -> None:
        super().__init__()

        self._images = images

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

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._listWidget)
        self.setLayout(layout)
