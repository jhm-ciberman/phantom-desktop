import threading
from dataclasses import dataclass
from typing import Callable

from PySide6 import QtCore

from .ImageProcessorService import ImageProcessorService
from .Models import Group, Image, Project


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
    All actions that have an effect on the project should be performed through the Workspace instance.
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

    groupsChanged = QtCore.Signal()
    """
    Signal emmited when all the groups changed. This signal is emitted when a group is added,
    removed, renamed, combined or the groups are cleared or recalculated.
    """

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

    def addImages(
            self, images: list[Image],
            onProgress: Callable[[int, int, Image], None] = None,
            onImageError: Callable[[Exception, Image], bool] = None):
        """
        Adds a list of images to the current project.

        Args:
            images (list[Image]): The list of images to add or the paths of the images to add.
                The images will be loaded from the disk if they are not already loaded.
            onProgress (Callable[[int, int, Image], None]): A callback that is called when an image
                is loaded (or failed to load). The callback receives the current index, the total
                number of images and the image that was loaded.
            onImageError (Callable[[Exception, Image], None]): A callback that is called when an
                image fails to load. The callback receives the exception and the image that failed
                to load. The callback should return True to skip the image and continue or False
                to stop the loading process. This callback is called before the onProgress callback.
        """
        onProgress = onProgress or (lambda index, total, image: None)
        onImageError = onImageError or (lambda e, image: False)
        imagesAdded = []
        count = len(images)
        for index, image in enumerate(images):
            try:
                image.load()  # If the image is already loaded, this is a no-op
            except Exception as e:
                if onImageError(e, image):
                    continue
                else:
                    break

            image.compute_hashes()
            self._project.add_image(image)
            imagesAdded.append(image)
            onProgress(index, count, image)
            self._addImageToBatch(image)
            self._imageProcessorService.process(image, self._onImageSuccess, self._onImageError)

        if len(imagesAdded) > 0:
            self.imagesAdded.emit(imagesAdded)
            self.setDirty(True)

    def removeImage(self, image: Image):
        """
        Removes an image from the current project.
        """
        self._project.remove_image(image)

        self.imagesRemoved.emit([image])
        self._removeImageFromBatch(image)
        self.setDirty(True)

    def removeImages(self, images: list[Image]):
        """
        Removes a list of images from the current project.
        """
        self._project.remove_images(images)

        self.imagesRemoved.emit(images)
        for image in images:
            self._removeImageFromBatch(image)
        self.setDirty(True)

    def _onImageSuccess(self, image: Image):
        """
        Callback called when an image is successfully processed.
        """
        self._addToGroupsIfNecessary(image)
        self.setDirty(True)  # This is because the image is modified by the ImageProcessor
        self.imageProcessed.emit(image)
        self._removeImageFromBatch(image)

    def _onImageError(self, error: Exception, image: Image):
        """
        Callback called when an image processing error occurs.
        """
        self.imageProcessingFailed.emit(image, error)
        self._removeImageFromBatch(image)

    def _addToGroupsIfNecessary(self, image: Image):
        # If the groups are not yet clustered, skip this step
        if len(self._project.groups) == 0:
            return

        # If the image has no faces, nothing to do here
        if len(image.faces) == 0:
            return

        # Add the faces to the best matching group (or create a new group)
        for face in image.faces:
            self._project.add_face_to_best_group(face)
        self.groupsChanged.emit()

    def mergeGroups(self, groupA: Group, groupB: Group):
        """
        Merges two groups into a single group.

        Args:
            groupA (Group): The first group.
            groupB (Group): The second group.
        """
        groupA.merge(groupB)
        self._project.remove_group(groupB)
        self.setDirty()
        self.groupsChanged.emit()

    def dontMergeGroups(self, groupA: Group, groupB: Group):
        """
        Marks two groups as not mergeable.

        Args:
            groupA (Group): The first group.
            groupB (Group): The second group.
        """
        groupA.dont_merge_with.add(groupB)
        groupB.dont_merge_with.add(groupA)
        self.setDirty()

    def recalculateGroups(self):
        """
        Recalculates the groups of the current project.
        """
        self._project.recalculate_groups()
        self.setDirty()
        self.groupsChanged.emit()

    def clearGroups(self):
        """
        Clears the groups of the current project.
        """
        self._project.clear_groups()
        self.setDirty()
        self.groupsChanged.emit()
