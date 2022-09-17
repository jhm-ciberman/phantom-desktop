import multiprocessing
from uuid import UUID
from src.Image import Image, Face, ImageFeatures
from PySide6 import QtCore
import threading
import dlib
from pkg_resources import resource_filename
from time import perf_counter_ns


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

    def _process_face(self, image_rgb: dlib.array, face_rect: dlib.rectangle) -> Face:
        """
        Process a single face in an image.

        Args:
            image_rgb (dlib.array): The image in RGB format.
            rect (dlib.rectangle): The face rectangle.

        Returns:
            The processed face.
        """
        w = face_rect.right() - face_rect.left()
        h = face_rect.bottom() - face_rect.top()
        face = Face(face_rect.left(), face_rect.top(), w, h)

        # predict face parts
        t = perf_counter_ns()
        shape = self._shape_predictor(image_rgb, face_rect)
        face.parts = shape.parts()
        face.predict_time = perf_counter_ns() - t

        # encode face
        t = perf_counter_ns()
        face.encoding = self._face_encoder.compute_face_descriptor(image_rgb, shape, self.predictor_jitter)
        face.encoding_time = perf_counter_ns() - t

        print("Times (ms): Total: {:.2f}, Predict: {:.2f}, Encode: {:.2f}".format(
            (face.predict_time + face.encoding_time) / 1e6,
            face.predict_time / 1e6,
            face.encoding_time / 1e6
        ))

        return face

    def process(self, image_rgb: dlib.array) -> ImageFeatures:
        """
        Processes an image and returns the image features.

        Args:
            image_rgb (dlib.array): The image in RGB format.
        """
        t = perf_counter_ns()

        faces = self._face_detector(image_rgb, 1)
        faces = [self._process_face(image_rgb, face) for face in faces]
        time = perf_counter_ns() - t

        return ImageFeatures(faces, time)


class _WorkerEvent:
    """
    Represents an event that is raised by the worker.
    """

    def __init__(self, uuid: UUID) -> None:
        """
        Initializes a new instance of the WorkerEvent class.

        Args:
            uuid (UUID): The image UUID.
        """
        self.uuid = uuid


class _WorkerSuccessEvent(_WorkerEvent):
    """
    Represents an event that is raised by the worker when an image is processed.
    """

    def __init__(self, uuid: UUID, features: ImageFeatures) -> None:
        """
        Initializes a new instance of the WorkerSuccessEvent class.

        Args:
            uuid (UUID): The image UUID.
            features (ImageFeatures): The image features.
        """
        super().__init__(uuid)
        self.features = features


class _WorkerFailureEvent(_WorkerEvent):
    """
    Represents an event that is raised by the worker when an image processing fails.
    """

    def __init__(self, uuid: UUID, error: Exception) -> None:
        """
        Initializes a new instance of the WorkerFailureEvent class.

        Args:
            uuid (UUID): The image UUID.
            error (Exception): The error.
        """
        super().__init__(uuid)
        self.error = error


class _WorkerTask:
    """
    Represents a task that is executed by the worker.
    """

    def __init__(self, uuid: UUID, image_rgb: dlib.array) -> None:
        """
        Initializes a new instance of the WorkerTask class.

        Args:
            uuid (UUID): The image UUID.
            image_rgb (dlib.array): The image in RGB format.
        """
        super().__init__()
        self.uuid = uuid
        self.image_rgb = image_rgb


class _Worker(multiprocessing.Process):
    """
    Process multiple images in a separate process. Two queues are ussed to comunicate:
    - The input queue is used to send images to the worker.
    - The event queue is used to send events from the worker.
    These queues should be provided by the main process.
    """

    def __init__(self, input_queue, event_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self._input_queue = input_queue  # type: multiprocessing.Queue[_WorkerTask]
        self._event_queue = event_queue  # type: multiprocessing.Queue[_WorkerEvent]
        self._image_processor = None  # This is lazy initialized because dlib cannot be pickled.

    def run(self):
        if self._image_processor is None:
            self._image_processor = _ImageProcessor()

        while True:
            task = self._input_queue.get()
            if task is None:  # Poison pill pattern
                break

            try:
                features = self._image_processor.process(task.image_rgb)
                event = _WorkerSuccessEvent(task.uuid, features)
            except Exception as e:
                event = _WorkerFailureEvent(task.uuid, e)

            self._event_queue.put(event)


class ImageFeaturesService(QtCore.QObject):
    """
    Singleton class that provides a simple interface to process multiple images in parallel
    using multiprocessing. The class is not thread safe and should be only used from the UI thread.

    Signals:
        onImageProcessed: Emitted when an image is processed.
        onImageError: Emitted when an error occurs while processing an image.
    """

    _instance = None

    onImageProcessed = QtCore.Signal(Image)

    onImageError = QtCore.Signal(Image, Exception)

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
                image.features = event.features
                self.onImageProcessed.emit(image)
            elif isinstance(event, _WorkerFailureEvent):
                self.onImageError.emit(image, event.error)

    def start(self) -> None:
        """
        Starts the image processing service.
        """
        if self._is_running:
            return

        for i in range(self._max_workers):
            name = "ImageFeaturesServiceWorker-{}".format(i)
            worker = _Worker(self._input_queue, self._event_queue, name=name, daemon=True)
            worker.start()
            self._workers.append(worker)

    def stop(self) -> None:
        """
        Stops the image processing service.
        """
        if not self._is_running:
            return

        for _ in range(self._max_workers):
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
        self._pending_images[image.uuid] = image
        self._input_queue.put(_WorkerTask(image.uuid, image.get_rgb()))

    def __del__(self):
        self.stop()

    def queue_size(self) -> int:
        """
        Returns the number of images in the queue.
        """
        return self._input_queue.qsize()
