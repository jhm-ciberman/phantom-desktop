from typing import Any
from phantom.faces import encode
from src.Image import Image, Face
from PySide6 import QtCore
import threading
import dlib
from queue import Queue
from pkg_resources import resource_filename
from time import perf_counter_ns

_path_encoder = resource_filename("phantom", "models/dlib_face_recognition_resnet_model_v1.dat")

_path_shape_68p = resource_filename("phantom", "models/shape_predictor_68_face_landmarks.dat")


class Pool:
    def __init__(self, factory_func) -> None:
        self._pool = []
        self._make = factory_func

    def acquire(self):
        """
        Gets a from the pool.
        """
        if len(self._pool) == 0:
            t = perf_counter_ns()
            result = self._make()
            print(f"Created new object (ms): {(perf_counter_ns() - t) / 1000000} ms (Result: {result})")
            return result

        return self._pool.pop()

    def release(self, pool_object) -> None:
        """
        Returns a detector to the pool.
        """
        self._pool.append(pool_object)


class LoadingWorker(QtCore.QObject):
    """
    A worker class for load the image metadata in separate threads in the background.
    This class is a singleton.

    Signals:
        on_image_processed (QtCore.Signal): Emitted when an image has been processed.
    """

    _instance = None

    on_image_processed = QtCore.Signal(Image)

    on_image_error = QtCore.Signal(Image, Exception)

    def __init__(self) -> None:
        """
        Initializes the LoadingWorker class.
        """
        super().__init__()
        self._uses_multithreading = True
        self._queue = Queue()  # type: Queue[Image]
        self._threads = []
        self._is_working = False
        self._max_workers = 1  # min(1, max(32, (os.cpu_count() or 1) + 4))

        # The models take between 50-1500ms to load, and they are not thread safe.
        # Therefore, we create a pool of models to use.
        # This way if we have N threads, we will lazy load N model instances and reuse them.
        self._face_detector_pool = Pool(dlib.get_frontal_face_detector)
        self._face_encoder_pool = Pool(lambda: dlib.face_recognition_model_v1(_path_encoder))
        self._shape_predictor_pool = Pool(lambda: dlib.shape_predictor(_path_shape_68p))

    @classmethod
    def instance(cls) -> "LoadingWorker":
        """
        Gets the singleton instance of the LoadingWorker class.
        """
        if cls._instance is None:
            cls._instance = LoadingWorker()
        return cls._instance

    def add_image(self, image: Image) -> None:
        """
        Adds an image to the queue.
        """
        self._queue.put(image)

    def _process_next(self) -> None:
        """
        Processes the next image in the queue.
        """
        while True:
            image = self._queue.get()
            try:
                self._process_image(image)
            except Exception as e:
                self.on_image_error.emit(image, e)
            self.on_image_processed.emit(image)

    def _process_image(self, image: Image) -> None:
        """
        Processes an image.
        """
        if image.processed:
            return
        print(f"Processing image: {image.path}")
        # detect faces
        t = perf_counter_ns()
        image_rgb = image.get_rgb()
        print(f"Converting to RGB (ms) {((perf_counter_ns() - t) / 1e6):.2f}")

        detector = self._face_detector_pool.acquire()
        t = perf_counter_ns()
        face_rectangles = detector(image_rgb, 1)
        print(f"Detecting faces (ms) {((perf_counter_ns() - t) / 1e6):.2f}")

        self._face_detector_pool.release(detector)

        face_predictor = self._shape_predictor_pool.acquire()
        face_encoder = self._face_encoder_pool.acquire()
        jitter = 1

        for rect in face_rectangles:
            w = rect.right() - rect.left()
            h = rect.bottom() - rect.top()
            face = Face(rect.left(), rect.top(), w, h)
            image.faces.append(face)

            # predict face parts
            t = perf_counter_ns()
            shape = face_predictor(image_rgb, rect)
            face.parts = shape.parts()
            face.predict_time = perf_counter_ns() - t

            # encode face
            t = perf_counter_ns()
            face.encoding = face_encoder.compute_face_descriptor(image_rgb, shape, jitter)
            face.encoding_time = perf_counter_ns() - t

            print("Times (ms): Total: {:.2f}, Predict: {:.2f}, Encode: {:.2f}".format(
                (face.predict_time + face.encoding_time) / 1e6,
                face.predict_time / 1e6,
                face.encoding_time / 1e6
            ))

        self._shape_predictor_pool.release(face_predictor)
        self._face_encoder_pool.release(face_encoder)

        image.processed = True

    def __del__(self) -> None:
        """
        Stops the worker.
        """
        self.stop()

    def start(self) -> None:
        """
        Starts the worker.
        """
        self._is_working = True
        for _ in range(self._max_workers):
            thread = threading.Thread(target=self._process_next, daemon=True)
            self._threads.append(thread)
            thread.start()

    def stop(self) -> None:
        """
        Stops the worker.

        Args:
            force (bool): If True, the worker will be stopped immediately.
        """
        self._is_working = False
        for thread in self._threads:
            thread.join()
        self._threads = []
