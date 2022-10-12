from dataclasses import dataclass
from typing import Callable
from PySide6 import QtCore
from .ImageProcessorService import ImageProcessorService
from .Models import Group, Image, Project
import threading


@dataclass(frozen=True, slots=True)
class BatchProgress:
    """
    An immutable class that represents the progress of a batch operation.
    """
    total: int = 0
    """The number of total tasks."""

    value: int = 0
    """The number of finished tasks."""

    @property
    def progress(self) -> float:
        """Returns the progress of the current batch."""
        return (self.value / self.total) if self.total > 0 else 0.0

    @property
    def isFinished(self) -> bool:
        """Returns True if all the tasks have been completed."""
        return self.total == self.value

    def advance(self) -> "BatchProgress":
        """Increments the finished count."""
        if self.total == self.value:
            return self
        return BatchProgress(self.total, self.value + 1)

    def incrementTotal(self) -> "BatchProgress":
        """Increments the total count. If all the tasks have been completed, the progress is reset."""
        if self.total == self.value:
            return BatchProgress(1, 0)
        else:
            return BatchProgress(self.total + 1, self.value)

    def reset(self) -> "BatchProgress":
        """Resets the progress."""
        return BatchProgress(0, 0)


class Workspace(QtCore.QObject):
    """
    A class that is responsible for managing a single opened project. The Workspace class manages
    the dirty state of the project and emits various signals when the project is changed or updated.
    It as a global channel for internal comunication between the different components of the application.
    A Workspace instance is created by the Application class. There is always one active Project per Workspace.
    """

    projectChanged = QtCore.Signal()
    """Signal emitted when the current project changes."""

    isDirtyChanged = QtCore.Signal(bool)
    """Signal emitted when the current project dirty state changes."""

    imagesAdded = QtCore.Signal(list)  # List[Image]
    """Signal emitted when one or more images are added to the project."""

    imagesRemoved = QtCore.Signal(list)  # List[Image]
    """Signal emitted when one or more images are removed from the project."""

    imageProcessed = QtCore.Signal(Image)
    """Signal emited when an image is processed successfully by the ImageProcessor."""

    imageProcessingFailed = QtCore.Signal(Image, Exception)
    """Signal emited when an image processing error occurs."""

    batchProgressChanged = QtCore.Signal(BatchProgress)
    """Signal emited when the progress of the batch processing changes."""

    def __init__(self, imageProcessorService: ImageProcessorService):
        """
        Initializes a new instance of the Workspace class.

        Args:
            imageProcessorService (ImageProcessorService): The image processor service.
        """
        super().__init__()
        self._imageProcessorService: ImageProcessorService = imageProcessorService
        self._project = Project()  # Empty project
        self._dirty = False
        self._batchLock = threading.Lock()  # Lock for the batch progress and the queue
        self._batchProgress = BatchProgress()
        self._queuedImages: set[Image] = set()

    def project(self) -> Project:
        """
        Returns the current project.
        """
        return self._project

    def setProject(self, project: Project):
        """
        Sets the current project.
        """
        self._project = project
        self._dirty = False
        self.projectChanged.emit()

    def isDirty(self) -> bool:
        """
        Returns True if the current project is dirty.
        """
        return self._dirty

    def setDirty(self, dirty: bool = True):
        """
        Sets the dirty state of the current project.
        """
        if self._dirty != dirty:
            self._dirty = dirty
            self.isDirtyChanged.emit(dirty)

    def queuedImages(self) -> frozenset[Image]:
        """
        Returns a set of images that are currently in the queue.
        """
        with self._batchLock:
            return frozenset(self._queuedImages)

    def _addImageToBatch(self, image: Image):
        """
        Adds an image to the batch.
        """
        with self._batchLock:
            if image not in self._queuedImages:
                self._queuedImages.add(image)
                self._batchProgress = self._batchProgress.incrementTotal()
                self.batchProgressChanged.emit(self._batchProgress)

    def _removeImageFromBatch(self, image: Image):
        """
        Removes an image from the batch.
        """
        with self._batchLock:
            if image in self._queuedImages:
                self._queuedImages.remove(image)
                self._batchProgress = self._batchProgress.advance()
                self.batchProgressChanged.emit(self._batchProgress)

    def batchProgress(self) -> BatchProgress:
        """
        Returns the current batch progress.
        """
        with self._batchLock:
            return self._batchProgress

    def closeProject(self):
        """
        Closes the current project.
        """
        pass

    def newProject(self):
        """
        Creates a new project.
        """
        self.setProject(Project())

    def openProject(self, path: str):
        """
        Opens an existing project.

        Args:
            path (str): The path of the project to open.
        """
        self.setProject(Project(path))

    def saveProject(self, path: str = None):
        """
        Saves the current project.

        Args:
            path (str): The path where to save the project. If None the project is saved to the
                current path.
        """
        if not path.endswith(".phantom"):
            path += ".phantom"
        self._project.save(path)
        self.setDirty(False)

    def addImage(self, imageOrPath: Image | str) -> Image:
        """
        Adds an image to the current project.

        Args:
            imageOrPath (Image | str): The image to add or the path of the image to add.
        """
        if isinstance(imageOrPath, str):
            image = Image(imageOrPath)

        self._project.add_image(image)

        self.imagesAdded.emit([image])
        self._addImageToBatch(image)
        self.setDirty(True)

        self._imageProcessorService.process(image, self._onImageSuccess, self._onImageError)
        return image

    def addImages(self, paths: list[str], onImageLoaded: Callable[[Image, int, int], None] = None):
        """
        Adds a list of images to the current project.

        Args:
            paths (list[str]): The paths of the images to add.
            onImageLoaded (Callable[[Image, int, int], None]): A callback that is called when an image
                is loaded. The callback receives the image, the index of the image in the list and the
                total number of images.
        """
        onImageLoaded = onImageLoaded or (lambda image, index, total: None)
        images = []
        count = len(paths)
        for index, path in enumerate(paths):
            image = Image(path)
            self._project.add_image(image)
            images.append(image)
            onImageLoaded(image, index, count)
            self._addImageToBatch(image)
            self._imageProcessorService.process(image, self._onImageSuccess, self._onImageError)

        self.imagesAdded.emit(images)
        self.setDirty(True)

    def removeImage(self, image: Image):
        """
        Removes an image from the current project.
        """
        self._project.remove_image(image)

        self.imagesRemoved.emit([image])
        self._removeImageFromBatch(image)
        self.setDirty(True)

    def _onImageSuccess(self, image: Image):
        """
        Callback called when an image is successfully processed.
        """
        self.setDirty(True)  # This is because the image is modified by the ImageProcessor

        self.imageProcessed.emit(image)
        self._removeImageFromBatch(image)

    def _onImageError(self, image: Image, error: Exception):
        """
        Callback called when an image processing error occurs.
        """
        self.imageProcessingFailed.emit(image, error)
        self._removeImageFromBatch(image)