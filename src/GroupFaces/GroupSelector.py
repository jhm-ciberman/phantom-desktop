from PySide6 import QtCore, QtGui, QtWidgets
from ..Widgets.GridBase import GridBase
from ..Models import Group
from ..l10n import __


class GroupSelector(QtWidgets.QDialog):
    """
    A widget that contains a list of groups and a search box. The groups are displayed
    with their main face.
    """

    def __init__(self, groups: list[Group], parent: QtWidgets.QWidget = None,
                 title: str = None, showNewGroupOption: bool = False) -> None:
        """
        Initialize a new instance of the _GroupSelector class.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.
            showNewGroupOption (bool): Whether to show the option to create a new group.
        """
        super().__init__(parent)

        self.setWindowTitle("Select a group" if title is None else title)
        self.setModal(True)
        self.resize(400, 400)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._searchBox = QtWidgets.QLineEdit()
        self._searchBox.setPlaceholderText(__("Search"))
        self._searchBox.textChanged.connect(self._onSearchTextChanged)
        self._searchBox.setClearButtonEnabled(True)
        layout.addWidget(self._searchBox)

        self._groupsGrid = GridBase()
        self._groupsGrid.setGridSize(QtCore.QSize(80, 80))
        self._groupsGrid.setIconSize(QtCore.QSize(64, 64))
        self._groupsGrid.itemClicked.connect(self._onGroupSelected)
        layout.addWidget(self._groupsGrid)

        selectCancelLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(selectCancelLayout)

        selectCancelLayout.addStretch()

        self._selectButton = QtWidgets.QPushButton(__("Select"))
        self._selectButton.setEnabled(False)
        self._selectButton.clicked.connect(self._onSelectClicked)
        selectCancelLayout.addWidget(self._selectButton)

        self._cancelButton = QtWidgets.QPushButton(__("Cancel"))
        self._cancelButton.clicked.connect(self._onCancelClicked)
        selectCancelLayout.addWidget(self._cancelButton)

        gridSize = self._groupsGrid.gridSize()
        if showNewGroupOption:
            pixmap = self._getNewGroupPixmap(gridSize.width(), gridSize.height())
            text = __("New group")
            self._groupsGrid.addItemCore(pixmap, text, Group())

        for group in groups:
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
            return item.data(QtCore.Qt.UserRole)
        return None

    def _getNewGroupPixmap(self, width: int, height: int) -> QtGui.QPixmap:
        """
        Get the pixmap for the new group option.

        Args:
            width (int): The width of the pixmap.
            height (int): The height of the pixmap.

        Returns:
            QPixmap: The pixmap.
        """
        pixmap = QtGui.QPixmap("res/img/add.png")
        pixmap = pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return pixmap

    @staticmethod
    def getGroup(groups: list[Group], parent: QtWidgets.QWidget = None,
                 title: str = None, showNewGroupOption: bool = False) -> Group:
        """
        Get a group from the user.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.
            showNewGroupOption (bool): Whether to show the option to create a new group.

        Returns:
            Group: The selected group, or None if the user cancelled.
        """
        dialog = GroupSelector(groups, parent, title, showNewGroupOption)
        if dialog.exec():
            return dialog.selectedGroup()
        return None

# The multigroup selector has the following features:
# - It can be used to select one or more groups.
# - A button "Select all" is available to select all groups.
# - A button "Select none" is available to deselect all groups.
# - A button "Select named" is available to select all groups that have a name.
# - The groups are displayed with their main face and a checkbox.


class MultiGroupSelector(QtWidgets.QDialog):
    """
    A widget that contains a list of groups and a search box. The groups are displayed
    with their main face and a checkbox.
    """

    def __init__(self, groups: list[Group], parent: QtWidgets.QWidget = None, title: str = None) -> None:
        """
        Initialize a new instance of the _MultiGroupSelector class.

        Args:
            groups (list[Group]): The groups to display.
            parent (QWidget): The parent widget.
            title (str): The title of the widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Select groups" if title is None else title)
        self.setModal(True)
        self.resize(400, 400)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self._searchBox = QtWidgets.QLineEdit()
        self._searchBox.setPlaceholderText(__("Search"))
        self._searchBox.textChanged.connect(self._onSearchTextChanged)
        self._searchBox.setClearButtonEnabled(True)
        layout.addWidget(self._searchBox)

        selectButtonsLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(selectButtonsLayout)

        self._selectAllButton = QtWidgets.QPushButton(__("Select all"))
        self._selectAllButton.clicked.connect(self._onSelectAllClicked)
        selectButtonsLayout.addWidget(self._selectAllButton)

        self._selectNoneButton = QtWidgets.QPushButton(__("Select none"))
        self._selectNoneButton.clicked.connect(self._onSelectNoneClicked)
        selectButtonsLayout.addWidget(self._selectNoneButton)

        self._selectNamedButton = QtWidgets.QPushButton(__("Select named"))
        self._selectNamedButton.clicked.connect(self._onSelectNamedClicked)
        selectButtonsLayout.addWidget(self._selectNamedButton)

        self._groupsGrid = GridBase()
        self._groupsGrid.setGridSize(QtCore.QSize(80, 80))
        self._groupsGrid.setIconSize(QtCore.QSize(64, 64))
        layout.addWidget(self._groupsGrid)

        selectCancelLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(selectCancelLayout)

        self._selectButton = QtWidgets.QPushButton(__("Accept"))
        self._selectButton.clicked.connect(self._onSelectClicked)

        self._cancelButton = QtWidgets.QPushButton(__("Cancel"))
        self._cancelButton.clicked.connect(self._onCancelClicked)

        selectCancelLayout.addStretch()
        selectCancelLayout.addWidget(self._selectButton)
        selectCancelLayout.addWidget(self._cancelButton)

        self._groups = groups
        self._populateGroups()
        self._onSelectAllClicked()

    def _populateGroups(self) -> None:
        """
        Populate the groups grid.
        """
        self._groupsGrid.clear()

        for group in self._groups:
            item = QtWidgets.QListWidgetItem()
            item.setText(group.name)
            item.setData(QtCore.Qt.UserRole, group)
            w, h = self._groupsGrid.iconSize().width(), self._groupsGrid.iconSize().height()
            item.setIcon(QtGui.QIcon(group.main_face.get_avatar_pixmap(w, h)))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self._groupsGrid.addItem(item)

    def _onSearchTextChanged(self, text: str) -> None:
        """
        Called when the search text changed.

        Args:
            text (str): The new text.
        """
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            if item is not None:
                if text == "" or text.lower() in item.text().lower():
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def _onSelectAllClicked(self) -> None:
        """
        Called when the "Select all" button is clicked.
        """
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            if item is not None:
                item.setCheckState(QtCore.Qt.Checked)

    def _onSelectNoneClicked(self) -> None:
        """
        Called when the "Select none" button is clicked.
        """
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            if item is not None:
                item.setCheckState(QtCore.Qt.Unchecked)

    def _onSelectNamedClicked(self) -> None:
        """
        Called when the "Select named" button is clicked.
        """
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            if item is not None:
                if item.text() != "":
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)

    def _onSelectClicked(self) -> None:
        """
        Called when the "Select" button is clicked.
        """
        self._selectedGroups = []
        for i in range(self._groupsGrid.count()):
            item = self._groupsGrid.item(i)
            if item is not None and item.checkState() == QtCore.Qt.Checked:
                group = item.data(QtCore.Qt.UserRole)
                if group is not None:
                    self._selectedGroups.append(group)

        self.accept()

    def _onCancelClicked(self) -> None:
        """
        Called when the "Cancel" button is clicked.
        """
        self._selectedGroups = []
        self.reject()

    def getSelectedGroups(self) -> list[Group]:
        """
        Get the selected groups.

        Returns:
            list[Group]: The selected groups.
        """
        return self._selectedGroups

    @staticmethod
    def getGroups(groups: list[Group], parent: QtWidgets.QWidget = None, title: str = None) -> list[Group]:
        """
        Get the selected groups.

        Args:
            groups (list[Group]): The available groups.
            parent (QWidget, optional): The parent widget. Defaults to None.
            title (str, optional): The dialog title. Defaults to None.

        Returns:
            list[Group]: The selected groups.
        """
        dialog = MultiGroupSelector(groups, parent, title)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            return dialog.getSelectedGroups()
        else:
            return []
