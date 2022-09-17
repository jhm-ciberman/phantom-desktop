import cv2
import os
from PySide6 import QtGui
import numpy as np


class Face:
    """
    Represents a face in an image.

    Attributes:
        x (int): The x coordinate of the face.
        y (int): The y coordinate of the face.
        width (int): The width of the face.
        height (int): The height of the face.
        encoding (numpy.ndarray): The encoding of the face.
        parts (dlib.points): The parts of the face.

    """
    def __init__(self, x: int, y: int, width: int, height: int,
                 encoding: np.ndarray = None, parts: list = None) -> None:
        """
        Initializes a new instance of the Face class.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.encoding = encoding
        self.parts = parts

    @classmethod
    def from_phantom_touple(cls, coordinates: tuple):
        """
        Creates a new instance of the Image class from a tuple.

        Args:
            coordinates (tuple): A touple with four values representing the x0, y0, x1, y1 coordinates of the face.
        """
        x, y = coordinates[0], coordinates[1]
        w, h = coordinates[2] - x, coordinates[3] - y
        return cls(x, y, w, h)

    def to_phantom_touple(self) -> tuple:
        """
        Converts the face to a touple.

        Returns:
            tuple: A touple with four values representing the x0, y0, x1, y1 coordinates of the face.
        """
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class Image:
    """
    The Image class is the main Phantom Desktop image model.
    It represents an image loaded into memory. This class
    holds metadata about the image, and provides methods for accessing the raw color
    bytes of the image. The raw color bytes are stored in RGBA format, with each
    channel being a uint8 array.

    Attributes:
        path (str): The full path to the image source.
        basename (str): The basename of the image source.
        raw_image (numpy.ndarray[numpy.uint8]): The raw image data in RGBA format.
        channels (int): The number of channels in the image source.
        width (int): The width of the image source.
        height (int): The height of the image source.
        processed (bool): Whether or not the image has been processed by the LoadingWorker.
        faces (list[Face]): The faces detected in the image.
    """

    def __init__(self, path: str, raw_image=None):
        """
        Initializes the Image class.

        Args:
            path (str): The full path to the image source.
            raw_image (numpy.ndarray[numpy.uint8]): The raw image data in RGBA format. If not provided,
              the image will be loaded from the path.
        """
        self.path = os.path.normpath(path)
        self.basename = os.path.basename(path)

        if raw_image is None:
            raw_image = cv2.imread(path, flags=cv2.IMREAD_UNCHANGED)
            if raw_image is None:
                raise Exception(f"Could not load image from path: {path}")
            raw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGBA)

        self.raw_image = raw_image
        self.faces = []  # type: list[Face]
        self._processed = False

    @property
    def channels(self):
        """
        Gets the number of channels in the image source.
        """
        return self.raw_image.shape[2]

    @property
    def width(self):
        """
        Gets the width of the image source.
        """
        return self.raw_image.shape[1]

    @property
    def height(self):
        """
        Gets the height of the image source.
        """
        return self.raw_image.shape[0]

    def save(self, path: str):
        """
        Saves the image to a path.
        """
        raw_bgra = cv2.cvtColor(self.raw_image, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(path, raw_bgra)

    @property
    def pixmap(self) -> QtGui.QPixmap:
        """
        Gets a QPixmap of the image.
        """
        return ImageCache.default().get_pixmap(self)

    @property
    def image(self) -> QtGui.QImage:
        """
        Gets a QImage of the image.
        """
        return ImageCache.default().get_image(self)

    @property
    def processed(self) -> bool:
        """
        Gets whether the image has been processed by the LoadingWorker.
        """
        return self._processed

    @processed.setter
    def processed(self, value: bool):
        """
        Sets whether the image has been processed by the LoadingWorker.
        """
        self._processed = value

    def get_rgb(self) -> np.ndarray:
        """
        Gets the raw image data in RGB format. (No alpha channel)
        """
        return cv2.cvtColor(self.raw_image, cv2.COLOR_RGBA2RGB)


class ImageCache:
    """
    Singleton class for storing QImage and QPixmap cached references in a central location.
    """
    _instance = None

    def __init__(self):
        self._image_cache = {}
        self._pixmap_cache = {}

    @staticmethod
    def default():
        """
        Gets the default ImageCache instance.
        """
        if ImageCache._instance is None:
            ImageCache._instance = ImageCache()
        return ImageCache._instance

    def get_image(self, image: Image):
        """
        Gets a QImage for the given Image object.
        """
        if image not in self._image_cache:
            self._image_cache[image] = QtGui.QImage(image.raw_image.data, image.width, image.height,
                                                    QtGui.QImage.Format_RGBA8888)
        return self._image_cache[image]

    def get_pixmap(self, image: Image):
        """
        Gets a QPixmap for the given Image object.
        """
        if image not in self._pixmap_cache:
            self._pixmap_cache[image] = QtGui.QPixmap.fromImage(self.get_image(image))
        return self._pixmap_cache[image]

    def clear(self):
        """
        Clears the cache.
        """
        self._image_cache.clear()
        self._pixmap_cache.clear()

    def clear_image(self, image: Image):
        """
        Clears the image from the cache.
        """
        if image in self._image_cache:
            del self._image_cache[image]

    def clear_pixmap(self, image: Image):
        """
        Clears the pixmap from the cache.
        """
        if image in self._pixmap_cache:
            del self._pixmap_cache[image]
