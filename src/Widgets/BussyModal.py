import threading
from typing import Callable

from PySide6 import QtCore, QtGui, QtWidgets

from ..l10n import __
from .LoadingIcon import LoadingIcon


class BussyModal(QtWidgets.QDialog):
    """
    A modal widget that can be used to indicate that the application is busy and perform some
    long-running task in the background.
    """

    # Used as a synchronization point for the thread to notify the main thread that the task is done.
    # This is needed because the task is performed in a separate thread and the main thread needs to
    # be notified when the task is done because calls to QT must be performed in the main thread.
    # Qt signals are thread safe by default.
    _taskDone = QtCore.Signal()

    def __init__(
            self, parent: QtWidgets.QWidget = None, task: Callable[[], None] = None,
            title: str = None, subtitle: str = None) -> None:
        """
        Initializes a new instance of the BussyModal class.

        Args:
            parent (QWidget): The parent widget.
            task (Callable[[], None]): The task to perform in the background.
            title (str): The title to display in the modal.
            subtitle (str): The subtitle to display in the modal.
        """
        super().__init__(parent)
        self._task = task
        self._loadingIcon = LoadingIcon(self)
        self._loadingIcon.setFixedSize(64, 64)
        self._taskDone.connect(self.close)

        titleSubtitleLayout = QtWidgets.QVBoxLayout()
        titleSubtitleLayout.setContentsMargins(0, 0, 0, 0)
        titleSubtitleLayout.setSpacing(0)

        self._title = QtWidgets.QLabel(self)
        self._title.setText(title or __("Working"))
        self._title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078d7;")
        self._title.setFixedHeight(30)
        titleSubtitleLayout.addWidget(self._title)

        self._subtitle = QtWidgets.QLabel(self)
        self._subtitle.setText(subtitle or __("Please wait..."))
        self._subtitle.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._subtitle.setStyleSheet("font-size: 14px; color: #666;")
        self._subtitle.setFixedHeight(20)
        titleSubtitleLayout.addWidget(self._subtitle)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.addWidget(self._loadingIcon)
        self._layout.addLayout(titleSubtitleLayout)
        self._layout.setContentsMargins(40, 40, 40, 40)
        self._layout.setSpacing(20)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)

        if self._task is not None:
            threading.Thread(target=self._runTaskAndSignal).start()

    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        super().hideEvent(event)

        self._task = None

    def _runTaskAndSignal(self) -> None:
        self._task()
        self._taskDone.emit()

    def task(self) -> Callable[[], None]:
        """
        Gets the task that is performed in the background.

        Returns:
            Callable[[], None]: The task that is performed in the background.
        """
        return self._task

    def setTask(self, value: Callable[[], None]) -> None:
        """
        Sets the task that is performed in the background.

        Args:
            value (Callable[[], None]): The task to perform in the background.
        """
        self._task = value

    def title(self) -> str:
        """
        Gets the title to display in the modal.

        Returns:
            str: The title to display in the modal.
        """
        return self._title.text()

    def setTitle(self, value: str) -> None:
        """
        Sets the title to display in the modal.

        Args:
            value (str): The title to display in the modal.
        """
        self._title.setText(value)

    def subtitle(self) -> str:
        """
        Gets the subtitle to display in the modal.

        Returns:
            str: The subtitle to display in the modal.
        """
        return self._subtitle.text()

    def setSubtitle(self, value: str) -> None:
        """
        Sets the subtitle to display in the modal.

        Args:
            value (str): The subtitle to display in the modal.
        """
        self._subtitle.setText(value)

    def exec(self, task: Callable[[], None] = None) -> int:
        """
        Shows the modal and performs the specified task in the background. This method blocks
        until the modal is closed.

        Args:
            task (Callable[[], None]): The task to perform in the background.

        Returns:
            int: The result of the modal.
        """
        if task is not None:
            self._task = task

        return super().exec()

    def open(self, task: Callable[[], None] = None) -> None:
        """
        Shows the modal and performs the specified task in the background.

        Args:
            task (Callable[[], None]): The task to perform in the background.
        """
        if task is not None:
            self._task = task

        super().open()

    def show(self, task: Callable[[], None] = None) -> None:
        """
        Shows the modal and performs the specified task in the background. 

        Args:
            task (Callable[[], None]): The task to perform in the background.
        """
        if task is not None:
            self._task = task

        super().show()

    def close(self) -> None:
        """
        Closes the modal.
        """
        self._task = None
        super().close()
