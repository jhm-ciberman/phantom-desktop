import multiprocessing
from uuid import UUID
from src.Image import Image, Face, Rect
import threading
import dlib
from pkg_resources import resource_filename
from time import perf_counter_ns
from dataclasses import dataclass
import queue
from src.EventBus import EventBus


@dataclass(frozen=True, slots=True)
class _ImageProcessorResult:
    """
    Represents the result of the image processor.

    Attributes:
        faces (list[Face]): The faces in the image.
        time (int): The time it took to process the image in nanoseconds.
    """
    faces: list[Face]
    time: int


class _ImageProcessor:
    """
    Service to process images. This class is not thread safe.
    Initializing a new instance of this class is bit expensive, so it is recommended
    to create a single instance and reuse it for multiple images.
    """

    _path_encoder = resource_filename("phantom", "models/dlib_face_recognition_resnet_model_v1.dat")

    _path_shape_68p = resource_filename("phantom", "models/shape_predictor_68_face_landmarks.dat")

    def __init__(self) -> None:
        """
        Initializes a new instance of the ImageProcessor class.
        """
        # The models take between 50-1500ms to load, and they are not thread safe.
        # So we need to create them in advance.
        self._face_detector = dlib.get_frontal_face_detector()
        self._face_encoder = dlib.face_recognition_model_v1(self._path_encoder)
        self._shape_predictor = dlib.shape_predictor(self._path_shape_68p)
        self.predictor_jitter = 0

    def _process_face(self, image_rgb: dlib.array, face_rect: dlib.rectangle, confidence: float) -> Face:
        """
        Process a single face in an image and returns a Face object.

        Args:
            image_rgb (dlib.array): The image in RGB format.
            face_rect (dlib.rectangle): The face rectangle.
            confidence (float): The face detection confidence score.

        Returns:
            The processed face.
        """

        face = Face()
        face.confidence = confidence

        x, y = face_rect.left(), face_rect.top()
        w, h = face_rect.right() - x, face_rect.bottom() - y
        face.aabb = Rect(x, y, w, h)

        # predict face parts
        t = perf_counter_ns()
        shape = self._shape_predictor(image_rgb, face_rect)
        face.shape = shape.parts()
        face.shape_time = perf_counter_ns() - t

        # encode face
        t = perf_counter_ns()
        face.encoding = self._face_encoder.compute_face_descriptor(image_rgb, shape, self.predictor_jitter)
        face.encoding_time = perf_counter_ns() - t

        return face

    def process(self, image_rgb: dlib.array) -> _ImageProcessorResult:
        """
        Processes an image and returns the image features.

        Args:
            image_rgb (dlib.array): The image in RGB format.
        """
        t = perf_counter_ns()

        detections, scores, _ = self._face_detector.run(image_rgb)
        faces = [self._process_face(image_rgb, face, score) for face, score in zip(detections, scores)]
        time = perf_counter_ns() - t

        return _ImageProcessorResult(faces, time)


@dataclass(frozen=True, slots=True)
class _WorkerEvent:
    """Represents an event that is raised by the worker."""
    uuid: UUID


@dataclass(frozen=True, slots=True)
class _WorkerSuccessEvent(_WorkerEvent):
    """Represents an event that is raised by the worker when an image is processed."""
    result: _ImageProcessorResult


@dataclass(frozen=True, slots=True)
class _WorkerFailureEvent(_WorkerEvent):
    """Represents an event that is raised by the worker when an image processing fails."""
    error: Exception


@dataclass(frozen=True, slots=True)
class _WorkerTask:
    """Represents a task that is executed by the worker."""
    uuid: UUID
    image_rgb: dlib.array


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
            self._image_processor = _ImageProcessor()

        while True:
            try:
                task = self._input_queue.get(timeout=self.max_idle_time)
            except queue.Empty:
                break

            if task is None:  # Poison pill pattern
                break

            try:
                result = self._image_processor.process(task.image_rgb)
                event = _WorkerSuccessEvent(task.uuid, result)
            except Exception as e:
                event = _WorkerFailureEvent(task.uuid, e)

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
        self._pending_images = {}  # type: dict[UUID, Image]
        self._workers = []  # type: list[_Worker]
        self._max_workers = multiprocessing.cpu_count()
        self._is_running = False

        self._event_queue_thread = threading.Thread(target=self._event_queue_worker, daemon=True)
        self._event_queue_thread.start()

    def _event_queue_worker(self):
        while True:
            event = self._event_queue.get()
            if event is None:  # Poison pill pattern
                break

            image = self._pending_images[event.uuid]
            del self._pending_images[event.uuid]

            if isinstance(event, _WorkerSuccessEvent):
                image.faces = event.result.faces
                image.faces_time = event.result.time
                image.processed = True
                EventBus.default().onImageProcessed.emit(image)
            elif isinstance(event, _WorkerFailureEvent):
                EventBus.default().onImageProcessingFailed.emit(image, event.error)

    def _addWorker(self) -> None:
        i = len(self._workers)
        name = "ImageFeaturesServiceWorker-{}".format(i)
        worker = _Worker(self._input_queue, self._event_queue, name=name, daemon=True)
        self._workers.append(worker)
        worker.start()

    def _addWorkerIfNeeded(self) -> bool:
        canAddWorker = self.workers_count() < self._max_workers
        hasPendingImages = len(self._pending_images) > 0

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
        if not self._is_running:
            return

        for _ in range(len(self._workers)):
            self._input_queue.put(None)
        for worker in self._workers:
            worker.join()
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
        Processes an image.
        """
        if image.uuid in self._pending_images:
            raise ValueError("Image is already being processed.")

        self._addWorkerIfNeeded()

        self._pending_images[image.uuid] = image
        self._input_queue.put(_WorkerTask(image.uuid, image.get_pixels_rgb()))

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
        return len(self._pending_images)

    def workers_count(self) -> int:
        """
        Returns the number of workers.
        """
        # First, remove all workers that are not running anymore.
        self._workers = [w for w in self._workers if w.is_alive()]
        return len(self._workers)
