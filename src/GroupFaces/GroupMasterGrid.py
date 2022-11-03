from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __
from ..Models import Group
from ..Widgets.GridBase import GridBase


class GroupMasterGrid(GridBase):
    """
    Widget that displays a list of groups of faces in form of a grid of thumbnails.
    """

    groupClicked = QtCore.Signal(Group)
    """Emited when a group is clicked."""

    combineGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Combine group with..." action is triggered"""

    renameGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Rename group" action is triggered"""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the _GroupsPreview class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self.setSizePreset(GridBase.smallPreset)

        self._groups = []  # type: list[Group]
        self.selectionModel().selectionChanged.connect(self._onSelectionChanged)
        self.itemDoubleClicked.connect(self._onItemDoubleClicked)

        self._combineGroupAction = QtGui.QAction(__("Combine group with..."), self)
        self._combineGroupAction.triggered.connect(self._onCombineGroupTriggered)

        self._renameGroupAction = QtGui.QAction(QtGui.QIcon("res/img/edit.png"), __("Rename group"), self)
        self._renameGroupAction.triggered.connect(self._onRenameGroupTriggered)

        self._contextMenu = QtWidgets.QMenu(self)
        self._contextMenu.addAction(self._combineGroupAction)
        self._contextMenu.addAction(self._renameGroupAction)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Called when the widget receives a context menu event.

        Args:
            event (QContextMenuEvent): The event.
        """
        self._contextMenu.exec_(event.globalPos())

    def setGroups(self, groups: list[Group]) -> None:
        """
        Set the groups to display.

        Args:
            groups (list[Group]): The groups to display.
        """
        self.clear()
        self._groups = groups.copy()
        # Sort groups by the following criteria:
        # 1. If the group has a name, it is displayed first.
        # 2. In second place, the group with the most faces is displayed.
        self._groups.sort(key=lambda group: (group.name != "", len(group.faces)), reverse=True)

        for group in self._groups:
            count = len(group.faces)
            if count == 0:
                continue
            w, h = self.iconSize().width(), self.iconSize().height()
            pixmap = group.main_face.get_avatar_pixmap(w, h)
            text = f"{group.name} ({count})" if group.name else f"({count})"            
            self.addItemCore(pixmap, text)

    def groups(self) -> list[Group]:
        """
        Get the groups that are displayed.

        Returns:
            list[Group]: The groups that are displayed.
        """
        return self._groups

    def selectGroup(self, group: Group) -> None:
        """
        Select the group in the grid.

        Args:
            group (Group): The group to select.
        """
        index = self._groups.index(group)
        self.setCurrentRow(index)

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemDoubleClicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """
        Called when an item is double-clicked.

        Args:
            item (QListWidgetItem): The item that was double-clicked.
        """
        self.renameGroupTriggered.emit(self._groups[self.row(item)])

    @QtCore.Slot()
    def _onCombineGroupTriggered(self) -> None:
        """
        Called when the "Combine group with..." action is triggered.
        """
        self.combineGroupTriggered.emit(self._groups[self.currentRow()])

    @QtCore.Slot()
    def _onRenameGroupTriggered(self) -> None:
        """
        Called when the "Rename group" action is triggered.
        """
        self.renameGroupTriggered.emit(self._groups[self.currentRow()])

    @QtCore.Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def _onSelectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        """
        Called when the selection changes.

        Args:
            selected (QItemSelection): The selected items.
            deselected (QItemSelection): The deselected items.
        """
        if selected.indexes():
            self.groupClicked.emit(self._groups[selected.indexes()[0].row()])
