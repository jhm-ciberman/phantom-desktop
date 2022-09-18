from PySide6 import QtCore, QtGui, QtWidgets
from .Image import Image
from .Services.ClusteringService import cluster


class GroupFacesWindow(QtWidgets.QWidget):
    def __init__(self, images: list[Image]) -> None:
        super().__init__()

        self._images = images

        self._gridSize = QtCore.QSize(250, 250)
        self._iconSize = QtCore.QSize(250, 230)
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

        faces = []
        for image in self._images:
            faces.extend(image.faces)

        groups = cluster(faces)

        for group in groups:
            if len(group.faces) == 0:
                continue

            face = group.faces[0]
            item = QtWidgets.QListWidgetItem()
            item.setText(group.name)
            self._listWidget.addItem(item)
            w, h = self._iconSize.width(), self._iconSize.height()
            pixmap = face.get_pixmap(w, h)
            icon = QtGui.QIcon(pixmap)
            item.setIcon(icon)
            label = "Faces: " + str(len(group.faces))
            item.setToolTip(label)
            item.setText(label)

        self._listWidget.itemSelectionChanged.connect(self._onItemSelectionChanged)
        self._listWidget.itemDoubleClicked.connect(self._onItemDoubleClicked)

    @QtCore.Slot()
    def _onItemSelectionChanged(self) -> None:
        pass

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemDoubleClicked(self, item: QtWidgets.QListWidgetItem) -> None:
        pass
