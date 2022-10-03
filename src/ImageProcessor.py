from time import perf_counter_ns

import numpy as np
from .Models import Face
from .Models import Rect
from dataclasses import dataclass
import dlib


@dataclass(frozen=True, slots=True)
class ImageProcessorResult:
    """
    Represents the result of the image processor.

    Attributes:
        faces (list[Face]): The faces in the image.
        time (int): The time it took to process the image in nanoseconds.
    """
    faces: list[Face]
    time: int


class ImageProcessor:
    """
    Service to process images. This class is not thread safe.
    Initializing a new instance of this class is bit expensive, so it is recommended
    to create a single instance and reuse it for multiple images.
    """

    _path_encoder = "./models/dlib_face_recognition_resnet_model_v1.dat"

    _path_shape_68p = "./models/shape_predictor_68_face_landmarks.dat"

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
        # Detect the face landmarks.
        shape = self._shape_predictor(image_rgb, face_rect)
        encoding = self._face_encoder.compute_face_descriptor(image_rgb, shape, self.predictor_jitter)

        # Return the face.
        face = Face()
        x, y = face_rect.left(), face_rect.top()
        w, h = face_rect.right() - x, face_rect.bottom() - y
        face.aabb = Rect(x, y, w, h)
        face.encoding = np.array(encoding)
        face.confidence = confidence
        return face

    def process(self, image_rgb: dlib.array) -> ImageProcessorResult:
        """
        Processes an image and returns the image features.

        Args:
            image_rgb (dlib.array): The image in RGB format.
        """
        t = perf_counter_ns()

        detections, scores, _ = self._face_detector.run(image_rgb)
        faces = [self._process_face(image_rgb, face, score) for face, score in zip(detections, scores)]

        time = perf_counter_ns() - t
        return ImageProcessorResult(faces, time)
