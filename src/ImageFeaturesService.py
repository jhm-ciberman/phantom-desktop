import multiprocessing
from uuid import UUID
import uuid
from .ImageProcessor import ImageProcessor, ImageProcessorResult
from .Models import Image
import threading
import dlib
from dataclasses import dataclass
import queue
from src.EventBus import EventBus


@dataclass(frozen=True, slots=True)
class _WorkerEvent:
    """Represents an event that is raised by the worker."""

    id: UUID
    """The UUID of the request"""


@dataclass(frozen=True, slots=True)
class _WorkerSuccessEvent(_WorkerEvent):
    """Represents an event that is raised by the worker when an image is processed."""

    result: ImageProcessorResult
    """The result of the image processing."""


@dataclass(frozen=True, slots=True)
class _WorkerFailureEvent(_WorkerEvent):
    """Represents an event that is raised by the worker when an image processing fails."""

    error: Exception
    """The error that occurred."""


@dataclass(frozen=True, slots=True)
class _WorkerTask:
    """Represents a task that is executed by the worker."""

    id: UUID
    """The UUID of the request."""
    image_rgb: dlib.array
    """The image in RGB format."""


class _Worker(multiprocessing.Process):
    """
    Process multiple images in a separate process. Two queues are ussed to comunicate:
    - The input queue is used to send images to the worker.
    - The event queue is used to send events from the worker.
    These queues should be provided by the main process.
    """

    def __init__(self, input_queue, event_queue, *args, **kwargs):
        """
        Initializes a new instance of the Worker class.

        Args:
            input_queue (multiprocessing.Queue): The input queue.
            event_queue (multiprocessing.Queue): The event queue.
        """
        super().__init__(*args, **kwargs)
        self.daemon = True
        self._input_queue = input_queue  # type: multiprocessing.Queue[_WorkerTask]
        self._event_queue = event_queue  # type: multiprocessing.Queue[_WorkerEvent]
        self._image_processor = None  # This is lazy initialized because dlib cannot be pickled.
        self.max_idle_time = 10  # seconds

    def run(self):
        """
        Runs the worker.
        """
        if self._image_processor is None:
            self._image_processor = ImageProcessor()

        while True:
            try:
                task = self._input_queue.get(timeout=self.max_idle_time)
            except queue.Empty:
                break

            if task is None:  # Poison pill pattern
                break

            try:
                result = self._image_processor.process(task.image_rgb)
                event = _WorkerSuccessEvent(task.id, result)
            except Exception as e:
                event = _WorkerFailureEvent(task.id, e)

            self._event_queue.put(event)


class ImageFeaturesService:
    """
    Singleton class that provides a simple interface to process multiple images in parallel
    using multiprocessing. The class is not thread safe and should be only used from the UI thread.
    """

    _instance = None

    @staticmethod
    def instance() -> "ImageFeaturesService":
        """
        Returns the singleton instance of the ImageProcessingService class.
        """
        if ImageFeaturesService._instance is None:
            ImageFeaturesService._instance = ImageFeaturesService()
        return ImageFeaturesService._instance

    def __init__(self) -> None:
        """
        Initializes a new instance of the ImageProcessingService class.
        This constructor is private, use the instance() method to get the singleton instance.
        """
        super().__init__()
        self._input_queue = multiprocessing.Queue()
        self._event_queue = multiprocessing.Queue()
        self._id_to_image: dict[UUID, Image] = {}
        self._image_to_id: dict[Image, UUID] = {}
        self._workers = []  # type: list[_Worker]
        self._max_workers = multiprocessing.cpu_count()
        self._is_running = False

        self._event_queue_thread = threading.Thread(target=self._event_queue_worker, daemon=True)
        self._event_queue_thread.start()

    def _event_queue_worker(self):
        while True:
            event = self._event_queue.get()  # type: _WorkerEvent
            if event is None:  # Poison pill pattern
                break

            image = self._id_to_image[event.id]
            del self._id_to_image[event.id]
            del self._image_to_id[image]

            if isinstance(event, _WorkerSuccessEvent):
                image.faces = event.result.faces
                image.faces_time = event.result.time
                image.processed = True
                EventBus.default().imageProcessed.emit(image)
            elif isinstance(event, _WorkerFailureEvent):
                EventBus.default().imageProcessingFailed.emit(image, event.error)

    def _addWorker(self) -> None:
        i = len(self._workers)
        name = "ImageFeaturesServiceWorker-{}".format(i)
        worker = _Worker(self._input_queue, self._event_queue, name=name, daemon=True)
        self._workers.append(worker)
        worker.start()

    def _addWorkerIfNeeded(self) -> bool:
        canAddWorker = self.workers_count() < self._max_workers
        hasPendingImages = len(self._id_to_image) > 0

        if canAddWorker and hasPendingImages:
            self._addWorker()
            return True

        return False

    def start(self) -> None:
        """
        Starts the image processing service.
        """
        if self._is_running:
            return

        self._is_running = True

        while self._addWorkerIfNeeded():
            pass

    def stop(self) -> None:
        """
        Stops the image processing service.
        """
        # TODO: I'm not sure this method works as expected.
        # Use the kill() method instead.
        if not self._is_running:
            return

        for _ in range(len(self._workers)):
            self._input_queue.put(None)
        for worker in self._workers:
            worker.join()
        self._workers.clear()

        self._event_queue.put(None)
        self._event_queue_thread.join()

    def terminate(self) -> None:
        """
        Terminates the image processing service.
        This method should be used instead of stop() when the main process is exiting.
        """
        if not self._is_running:
            return

        for worker in self._workers:
            worker.terminate()
        self._workers.clear()

        self._event_queue.put(None)
        self._event_queue_thread.join()

    @property
    def is_running(self) -> bool:
        """
        Returns if the image processing service is running.
        """
        return self._is_running

    def process(self, image: Image) -> None:
        """
        Processes an image. This method is non-blocking and not thread safe.

        Args:
            image: The image to process.
        """
        if image.processed:
            return  # Image is already processed.

        if image in self._image_to_id:
            raise ValueError("Image is already being processed.")

        self._addWorkerIfNeeded()

        # generate new a random uuid for this request.
        # This id is used to comunicate with the worker process.
        id = uuid.uuid4()
        self._image_to_id[image] = id
        self._id_to_image[id] = image
        self._input_queue.put(_WorkerTask(id, image.get_pixels_rgb()))

    def __del__(self):
        self.stop()

    def queue_size(self) -> int:
        """
        Returns the number of images in the queue.
        """
        return self._input_queue.qsize()

    def pending_images_count(self) -> int:
        """
        Returns the number of images being processed.
        """
        return len(self._id_to_image)

    def workers_count(self) -> int:
        """
        Returns the number of workers.
        """
        # First, remove all workers that are not running anymore.
        self._workers = [w for w in self._workers if w.is_alive()]
        return len(self._workers)
