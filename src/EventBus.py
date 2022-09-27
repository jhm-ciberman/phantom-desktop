from PySide6 import QtCore
from .Image import Image


class EventBus(QtCore.QObject):
    """
    This singleton class acts as a global channel for internal comunication between the different
    components of the application. This class uses the "EventBus" design pattern. It extends the
    QObject class to be able to use the Qt signal/slot mechanism this means all the events are
    thread-safe.
    """

    _default = None  # Singleton

    onImageProcessed = QtCore.Signal(Image)
    """Raised when an image is processed successfully."""

    onImageProcessingFailed = QtCore.Signal(Image, Exception)
    """Raised when an image processing error occurs."""

    @staticmethod
    def default() -> "EventBus":
        """Gets the default EventBus instance."""
        if EventBus._default is None:
            EventBus._default = EventBus()
        return EventBus._default
