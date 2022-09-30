from PySide6 import QtCore, QtWidgets


def setSplitterStyle(splitter: QtWidgets.QSplitter):
    """
    Set the style of a splitter to a drag handle image.
    This helper is required due to a bug in Qt where the splitter is invisible.

    Args:
        splitter (QSplitter): The splitter to set the style for.
    """
    if splitter.orientation() == QtCore.Qt.Horizontal:
        splitter.setStyleSheet("QSplitter::handle { image: url(res/drag_handle_horizontal.png); }")
    else:
        splitter.setStyleSheet("QSplitter::handle { image: url(res/drag_handle_vertical.png); }")
