import string
import cv2
import os

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
    def __init__(self, path: str, raw_image):
        """
        Initializes the Image class.
        """
        self.path = path
        self.raw_image = raw_image
        self.basename = os.path.basename(path)

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

    @staticmethod
    def from_path(path: str):
        """
        Loads an image from a path.
        """
        raw_image = cv2.imread(path, flags=cv2.IMREAD_UNCHANGED)
        raw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGBA)
        return Image(path, raw_image)

