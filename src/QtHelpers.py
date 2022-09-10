from PySide6 import QtCore, QtWidgets


def setSplitterStyle(splitter: QtWidgets.QSplitter):
    # The splitter is invisible due to a bug in Qt so we use an image instead.
    if splitter.orientation() == QtCore.Qt.Horizontal:
        splitter.setStyleSheet("QSplitter::handle { image: url(res/drag_handle_horizontal.png); }")
    else:
        splitter.setStyleSheet("QSplitter::handle { image: url(res/drag_handle_vertical.png); }")
