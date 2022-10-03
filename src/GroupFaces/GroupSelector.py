from PySide6 import QtCore, QtWidgets
from ..Widgets.GridBase import GridBase
from ..Models import Group


class GroupSelector(QtWidgets.QDialog):
    """
    A widget that contains a list of groups and a search box. The groups are displayed
    with their main face.
    """

    def __init__(self, groups: list[Group], parent: QtWidgets.QWidget = None, title: str = None) -> None:
        """
        Initialize a new instance of the _GroupSelector class.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Select a group" if title is None else title)
        self.setModal(True)
        self.resize(400, 400)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._searchBox = QtWidgets.QLineEdit()
        self._searchBox.setPlaceholderText("Search")
        self._searchBox.textChanged.connect(self._onSearchTextChanged)
        self._searchBox.setClearButtonEnabled(True)
        layout.addWidget(self._searchBox)

        self._groupsGrid = GridBase()
        self._groupsGrid.itemClicked.connect(self._onGroupSelected)
        layout.addWidget(self._groupsGrid)

        selectCancelLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(selectCancelLayout)

        selectCancelLayout.addStretch()

        self._selectButton = QtWidgets.QPushButton("Select")
        self._selectButton.setEnabled(False)
        self._selectButton.clicked.connect(self._onSelectClicked)
        selectCancelLayout.addWidget(self._selectButton)

        self._cancelButton = QtWidgets.QPushButton("Cancel")
        self._cancelButton.clicked.connect(self._onCancelClicked)
        selectCancelLayout.addWidget(self._cancelButton)

        for group in groups:
            gridSize = self._groupsGrid.gridSize()
            pixmap = group.main_face.get_avatar_pixmap(gridSize.width(), gridSize.height())
            text = group.name if group.name else ""
            self._groupsGrid.addItemCore(pixmap, text, group)

    def _onSearchTextChanged(self, text: str) -> None:
        """
        Called when the search text changes.

        Args:
            text (str): The new text.
        """
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            group = item.data(QtCore.Qt.UserRole)  # type: Group
            name = group.name.lower() if group.name else ""
            item.setHidden(text.lower() not in name)

    def _onGroupSelected(self) -> None:
        """
        Called when a group is selected.
        """
        item = self._groupsGrid.currentItem()
        group = item.data(QtCore.Qt.UserRole)  # type: Group
        self._selectButton.setEnabled(group is not None)

    @QtCore.Slot()
    def _onSelectClicked(self) -> None:
        """
        Called when the select button is clicked.
        """
        self.accept()

    @QtCore.Slot()
    def _onCancelClicked(self) -> None:
        """
        Called when the cancel button is clicked.
        """
        self.reject()

    def selectedGroup(self) -> Group:
        """
        Get the selected group.

        Returns:
            Group: The selected group.
        """
        item = self._groupsGrid.selectedItems()[0]
        if item is not None:
            return item.data(QtCore.Qt.UserRole)  # type: Group
        return None

    @staticmethod
    def getGroup(groups: list[Group], parent: QtWidgets.QWidget = None, title: str = None) -> Group:
        """
        Get a group from the user.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.

        Returns:
            Group: The selected group.
        """
        dialog = GroupSelector(groups, parent, title)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            return dialog.selectedGroup()
        return None
