import string
import cv2
import os
from PySide6 import QtGui, QtCore, QtWidgets

class Image:
    """
    The Image class represents an image loaded into memory. This class
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
    """
    def __init__(self, path: str, raw_image = None):
        """
        Initializes the Image class.

        Args:
            path (str): The full path to the image source.
            raw_image (numpy.ndarray[numpy.uint8]): The raw image data in RGBA format. If not provided, the image will be loaded from the path.
        """
        self.path = os.path.normpath(path)
        self.basename = os.path.basename(path)

        if raw_image is None:
            raw_image = cv2.imread(path, flags=cv2.IMREAD_UNCHANGED)
            if raw_image is None:
                raise Exception(f"Could not load image from path: {path}")
            raw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGBA)
            
        self.raw_image = raw_image

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
    def pixmap(self):
        """
        Gets a QPixmap of the image.
        """
        return ImageCache.default().get_pixmap(self)

    @property
    def image(self):
        """
        Gets a QImage of the image.
        """
        return ImageCache.default().get_image(self)

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
            self._image_cache[image] = QtGui.QImage(image.raw_image.data, image.width, image.height, QtGui.QImage.Format_RGBA8888)
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