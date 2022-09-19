from PySide6 import QtWidgets


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


class PropertiesTable(QtWidgets.QTableWidget):
    """
    A widget that shows a table with "Property" and "Value" columns. It can display headers
    and perform basic formating.
    """

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the PropertiesTable class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Property", "Value"])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(20)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setShowGrid(False)
        self.setContentsMargins(5, 5, 5, 5)

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
        self.setItem(row, 0, QtWidgets.QTableWidgetItem(text))

    def addRow(self, key: str, value: str):
        """
        Adds a row to the inspector panel with the given key and value.

        Args:
            key (str): The key to show in the first column.
            value (str): The value to show in the second column.
        """
        row = self.rowCount()
        self.insertRow(row)
        value = str(value) if value is not None else "—"  # em dash
        keyItem = QtWidgets.QTableWidgetItem(key)
        valueItem = QtWidgets.QTableWidgetItem(value)
        valueItem.setToolTip(value)
        self.setItem(row, 0, keyItem)
        self.setItem(row, 1, valueItem)

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

    def clear(self):
        """
        Clears the inspector panel.
        """
        self.clearContents()
        self.setRowCount(0)
