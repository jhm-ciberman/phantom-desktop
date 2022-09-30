from PySide6 import QtCore, QtGui, QtWidgets
from ..Widgets.GridBase import GridBase
from ..Models import Group


class GroupsGrid(GridBase):
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
        self._groups = []  # type: list[Group]
        self.itemClicked.connect(self._onItemClicked)
        self.itemDoubleClicked.connect(self._onItemDoubleClicked)

        self._combineGroupAction = QtGui.QAction("Combine group with...", self)
        self._combineGroupAction.triggered.connect(self._onCombineGroupTriggered)

        self._renameGroupAction = QtGui.QAction(QtGui.QIcon("res/edit.png"), "Rename group", self)
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
        # Sort groups by number of faces in them, so that the largest groups are at the top
        self._groups.sort(key=lambda g: len(g.faces), reverse=True)

        for group in self._groups:
            if len(group.faces) == 0:
                continue
            w, h = self.iconSize().width(), self.iconSize().height()
            pixmap = group.main_face.get_avatar_pixmap(w, h)
            text = group.name if group.name else ""
            self.addItemCore(pixmap, text)

    def updateGroup(self, group: Group) -> None:
        """
        Update the group in the grid.

        Args:
            group (Group): The group to update.
        """
        index = self._groups.index(group)
        item = self.item(index)
        if item is None:
            return
        w, h = self.iconSize().width(), self.iconSize().height()
        pixmap = group.main_face.get_avatar_pixmap(w, h)
        text = group.name if group.name else ""
        self.setItemCore(item, pixmap, text)

    def removeGroup(self, group: Group) -> None:
        """
        Remove the group from the grid.

        Args:
            group (Group): The group to remove.
        """
        index = self._groups.index(group)
        self.takeItem(index)
        self._groups.remove(group)

    def groups(self) -> list[Group]:
        """
        Get the groups that are displayed.

        Returns:
            list[Group]: The groups that are displayed.
        """
        return self._groups

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _onItemClicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """
        Called when an item is clicked.

        Args:
            item (QListWidgetItem): The item that was clicked.
        """
        self.groupClicked.emit(self._groups[self.row(item)])

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
