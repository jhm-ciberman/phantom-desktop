from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __


class _Header(QtWidgets.QWidget):
    """
    A header for the PropertiesTable. The header shows in bold text and has a blue line decoration that extends to the right.
    """
    def __init__(self, text: str):
        """
        Initializes the Header class.
        """
        super().__init__()

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(10, 0, 10, 0)
        self.setLayout(self._layout)

        self._label = QtWidgets.QLabel(text)
        self._label.setStyleSheet("font-weight: bold; color: #0b3e66; margin-right: 5px;")
        self._layout.addWidget(self._label)

        self._line = QtWidgets.QFrame()
        self._line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self._line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._line.setStyleSheet("color: #0078d7;")
        self._layout.addWidget(self._line)


class _AbstractValueCell(QtWidgets.QTableWidgetItem):
    """
    A cell that shows a value.
    """

    def __init__(self, value: Any = None):
        """
        Initializes the ValueCell class.

        Args:
            value: The value to show.
        """
        super().__init__()
        self._originalValue = value

    def originalValue(self) -> str:
        """
        Gets the original value.
        """
        return self._originalValue


class _TextValueCell(_AbstractValueCell):
    """
    A cell that shows a value.
    """
    def __init__(self, value: Any = None):
        """
        Initializes the ValueCell class.
        """
        super().__init__(value)
        value = str(value) if value is not None else "—"  # em dash
        self.setText(value)
        self.setToolTip(value)


class _KeyCell(QtWidgets.QTableWidgetItem):
    """
    A cell that shows a key.
    """
    pass


class _InfoCell(QtWidgets.QTableWidgetItem):
    """
    A cell that shows an info text.
    """
    pass


class _PixmapValueCell(_AbstractValueCell):
    """
    A cell that shows a pixmap.
    """
    def __init__(self, pixmap: QtGui.QPixmap, value: Any = None):
        """
        Initializes the PixmapValueCell class.
        """
        super().__init__(value)
        self._pixmap = pixmap
        self.setData(QtCore.Qt.ItemDataRole.DecorationRole, pixmap)


class PropertiesTable(QtWidgets.QTableWidget):
    """
    A widget that shows a table with "Property" and "Value" columns. It can display headers
    and perform basic formating. It also provides a context menu with a "Copy" action.
    """

    selectedValueChanged = QtCore.Signal()
    """Signal emited when the selected value changes."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the PropertiesTable class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels([__("Property"), __("Value")])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(20)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setContentsMargins(5, 5, 5, 5)

        self.setIconSize(QtCore.QSize(64, 64))

        self._menu = QtWidgets.QMenu()
        copyAction = self._menu.addAction(__("Copy"))
        copyAction.triggered.connect(self.copy)

        self.itemSelectionChanged.connect(self._onSelectionChanged)

    def contextMenuEvent(self, e: QtGui.QContextMenuEvent) -> None:
        """
        Handles the context menu event.

        Args:
            e (QContextMenuEvent): The event.
        """
        if len(self.selectedItems()) > 0:
            self._menu.exec_(e.globalPos())

    @QtCore.Slot()
    def copy(self):
        """
        Copies the selected text to the clipboard.
        """
        selected = self.selectedItems()
        if len(selected) == 0:
            return
        if len(selected) == 2:  # 2 because we have 2 columns
            # if only one item is selected, just care about the value, not the key
            text = selected[1].text()
        else:
            # if multiple items are selected, copy the key and value of each item
            # in a tab-separated format. Example:
            # Key1    Value1\n
            # Key2    Value2\n
            # ...
            text = ""
            for item in selected:
                if item is None:
                    continue
                if isinstance(item, _KeyCell):
                    text += item.text() + "\t"
                elif isinstance(item, _TextValueCell):
                    text += item.text() + "\n"
                elif isinstance(item, _InfoCell):
                    text += item.text() + "\n"
                elif isinstance(item, _PixmapValueCell):
                    text += "\n"
            text = text[:-1]  # remove the last newline
        QtWidgets.QApplication.clipboard().setText(text)

    def addInfo(self, text: str):
        """
        Adds an info line to the table. The info line is a row with
        a single cell that spans both columns.

        Args:
            text (str): The text to show in the info line.
        """
        row = self.rowCount()
        self.insertRow(row)
        self.setSpan(row, 0, 1, 2)
        self.setItem(row, 0, _InfoCell(text))

    def addRow(self, key: str, value: str):
        """
        Adds a row to the inspector panel with the given key and value.

        Args:
            key (str): The key to show in the first column.
            value (str): The value to show in the second column.
        """
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, _KeyCell(key))
        self.setItem(row, 1, _TextValueCell(value))

    def addHeader(self, text: str):
        """
        Adds a header to the inspector panel. The header shows in bold text and has a
        blue line decoration that extends to the right.

        Args:
            text (str): The text to show in the header.
        """
        header = _Header(text)
        row = self.rowCount()
        self.insertRow(row)
        self.setSpan(row, 0, 1, 2)
        self.setCellWidget(row, 0, header)

    def addPixmapRow(self, key: str, pixmap: QtGui.QPixmap, value: Any = None):
        """
        Adds a row to the inspector panel with the given key and pixmap.

        Args:
            key (str): The key to show in the first column.
            pixmap (QPixmap): The pixmap to show in the second column.
        """
        row = self.rowCount()
        self.insertRow(row)
        self.setRowHeight(row, pixmap.height())
        self.setItem(row, 0, _KeyCell(key))
        self.setItem(row, 1, _PixmapValueCell(pixmap, value))

    def clear(self):
        """
        Clears the inspector panel.
        """
        self.clearContents()
        self.setRowCount(0)

    @QtCore.Slot()
    def _onSelectionChanged(self):
        """
        Called when the selection changes.
        """
        if self._infoProvider is None:
            return
        items = self.selectedItems()

        value = None
        if len(items) == 2:  # 2 because we have 2 columns
            for item in items:
                if isinstance(item, _AbstractValueCell):
                    value = item.originalValue()
                    break

        self._infoProvider.onSelectedValueChanged(self, value)
