import cv2
import os
from PySide6 import QtGui, QtCore
import numpy as np
from uuid import UUID, uuid4


class Rect:
    """
    Represents a rectangle
    """

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        """
        Initializes a new instance of the Rect class.

        Args:
            x (int): The x coordinate of the rectangle.
            y (int): The y coordinate of the rectangle.
            width (int): The width of the rectangle.
            height (int): The height of the rectangle.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"Rect(x={self.x}, y={self.y}, width={self.width}, height={self.height})"

    def fit_contains(self, max_width: int, max_height: int) -> "Rect":
        """
        Fits the rectangle into the given width and height preserving the aspect ratio.

        Args:
            max_width (int): The maximum width.
            max_height (int): The maximum height.

        Returns:
            Rect: A new rectangle that fits into the given width and height.
        """
        aspect_ratio = self.width / self.height
        new_width = max_width
        new_height = int(max_width / aspect_ratio)
        if new_height > max_height:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)

        x = int((max_width - new_width) / 2)
        y = int((max_height - new_height) / 2)
        return Rect(x, y, new_width, new_height)


class Face:
    """
    Represents a face in an image. This class is pickleable.

    Attributes:
        uuid (uuid.UUID): The unique identifier of the face.
        score (float): The score of the face according to the face recognition model.
        aabb (Rect): The axis-aligned bounding box of the face.
        encoding (numpy.ndarray): The encoding of the face.
        shape (dlib.points): A list of points representing the shape of the face.
        predict_time (int): The time it took to predict the face parts in nanoseconds.
        encoding_time (int): The time it took to encode the face parts in nanoseconds.
        image (Image): The image the face belongs to (None if the face is not part of an image).
        confidence (float): The confidence score of the face.

    """
    def __init__(self, uuid: UUID = None) -> None:
        """
        Initializes a new instance of the Face class.
        """
        self.uuid = uuid if uuid is not None else uuid4()
        self._aabb = None
        self.encoding = None
        self.shape = None
        self.shape_time = -1
        self.encoding_time = -1
        self.image = None  # type: Image
        self.confidence = 0.0  # type: float

    def __repr__(self) -> str:
        return "Face(uuid={}, confidence={}, aabb={})".format(self.uuid, self.confidence, self.aabb)

    @property
    def aabb(self) -> Rect:
        """
        Gets the axis-aligned bounding box of the face.
        """
        if self._aabb is not None:
            return self._aabb

        if self.shape is None:
            raise Exception("The face shape is not set.")

        p = self.shape[0]
        x0, y0 = p.x, p.y
        x1, y1 = p.x, p.y

        for p in self.shape:
            x0 = min(x0, p.x)
            y0 = min(y0, p.y)
            x1 = max(x1, p.x)
            y1 = max(y1, p.y)

        self._aabb = Rect(x0, y0, x1 - x0, y1 - y0)
        return self._aabb

    @aabb.setter
    def aabb(self, value: Rect) -> None:
        """
        Sets the axis-aligned bounding box of the face.
        """
        self._aabb = value

    def get_square_pixmap(self, size: int = 256, padding: float = 0.5) -> QtGui.QPixmap:
        """
        Gets a square pixmap of the face.

        Args:
            size (int): The size of the pixmap.
            padding (float): The padding factor. This is proportional to the size of the face.

        Returns:
            QtGui.QPixmap: The pixmap.
        """
        return self.get_pixmap(size, size, padding)

    def get_pixmap(self, width: int = 256, height: int = 256, padding: float = 0.5) -> QtGui.QPixmap:
        """
        Gets a pixmap of the face. The face will be scaled to fit the width and height
        preserving the aspect ratio.

        Args:
            width (int): The width of the pixmap.
            height (int): The height of the pixmap.
            padding (float): The padding factor. This is proportional to the size of the face.

        Returns:
            QtGui.QPixmap: The pixmap.
        """
        if self.image is None:
            raise Exception("The face is not part of an image.")

        # get the face rectangle
        aabb = self.aabb
        scale = max(aabb.width, aabb.height)
        padding = int(scale * padding)

        pixmap = self.image.get_pixmap()
        pixmap = pixmap.copy(aabb.x - padding, aabb.y - padding, scale + padding * 2, scale + padding * 2)
        pixmap = pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return pixmap

    def get_avatar_pixmap(self, width: int = 256, height: int = None) -> QtGui.QPixmap:
        """
        Gets a square pixmap of the face with a circular mask.

        Args:
            width (int): The width of the pixmap.
            height (int): The height of the pixmap. If None, the height will be set to the width.

        Returns:
            QtGui.QPixmap: The pixmap.
        """
        height = width if height is None else height
        pixmap = self.get_pixmap(width, height)
        mask = QtGui.QPixmap(pixmap.size())
        mask.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(mask)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtCore.Qt.white)
        painter.drawEllipse(0, 0, mask.width(), mask.height())
        painter.end()
        pixmap.setMask(mask.mask())
        return pixmap


class Group:
    """
    Represents a group of faces.

    Attributes:
        centroid (numpy.ndarray): The centroid of the group.
        faces (list[Face]): The faces in the group.
        name (str): The name of the group.
        main_face (Face): The face that is the most representative of the group.
          By default, the face with the highest confidence score is returned.
        main_face_override (Face): Overrides the main_face property.
    """

    def __init__(self, faces: list[Face] = None, name: str = None) -> None:
        """
        Initializes the Group class.

        Args:
            centroid (numpy.ndarray): The centroid of the group.
        """
        self.centroid = None  # type: np.ndarray
        self._faces = faces if faces is not None else []  # type: list[Face]
        self.name = name  # type: str
        self.main_face_override = None  # type: Face

    @property
    def main_face(self) -> Face:
        """
        Gets the face that is the most representative of the group.
        This face can be overridden by setting the main_face_override property.
        By default, the face with the highest confidence score is returned.
        """
        if self.main_face_override is not None:
            return self.main_face_override

        return max(self._faces, key=lambda face: face.confidence)

    @property
    def faces(self) -> list[Face]:
        """
        Gets the faces in the group.
        """
        return self._faces

    def count_unique_images(self) -> int:
        """
        Gets the number of unique images the group is part of.

        Returns:
            int: The number of unique images.
        """
        return len(set([face.image for face in self._faces]))

    def add_face(self, face: Face) -> None:
        """
        Adds a face to the group.

        Args:
            face (Face): The face to add.
        """
        self._faces.append(face)

    def remove_face(self, face: Face) -> None:
        """
        Removes a face from the group.

        Args:
            face (Face): The face to remove.
        """
        if self.main_face_override == face:
            self.main_face_override = None

        self._faces.remove(face)

    def clear_faces(self) -> None:
        """
        Removes all faces from the group.
        """
        self._faces.clear()
        self.main_face_override = None

    def merge(self, other: "Group") -> None:
        """
        Merges another group into this group.

        Args:
            other (Group): The group to merge.
        """
        # Combine faces
        self._faces.extend(other.faces)

        # Copy name if target group has no name
        if not self.name:
            self.name = other.name

        # Copy the main face override if target group has no main face override
        if not self.main_face_override:
            self.main_face_override = other.main_face_override


class Image:
    """
    The Image class is the main Phantom Desktop image model.
    It represents an image loaded into memory. This class
    holds metadata about the image, and provides methods for accessing the raw color
    bytes of the image. The raw color bytes are stored in RGBA format, with each
    channel being a uint8 array.

    Attributes:
        full_path (str): The full path to the image source.
        basename (str): The basename of the image source.
        folder_path (str): The folder path of the image source.
        raw_image (numpy.ndarray[numpy.uint8]): The raw image data in RGBA format.
        channels (int): The number of channels in the image source.
        width (int): The width of the image source.
        height (int): The height of the image source.
        faces (list[Face]): The faces in the image.
        faces_time (int): The time it took to process the faces in nanoseconds.
        processed (bool): Whether or not the image has been processed by the face detector.
    """

    def __init__(self, path: str, raw_image=None):
        """
        Initializes the Image class.

        Args:
            path (str): The path to the image source (can be relative or absolute).
            raw_image (numpy.ndarray[numpy.uint8]): The raw image data in RGBA format. If not provided,
              the image will be loaded from the path.
        """
        self.uuid = uuid4()
        self.full_path = os.path.abspath(path)

        if raw_image is None:
            raw_image = cv2.imread(path, flags=cv2.IMREAD_UNCHANGED)
            if raw_image is None:
                raise Exception(f"Could not load image from path: {path}")
            raw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGBA)

        self._raw_image = raw_image
        self._faces = []  # type: list[Face]
        self.faces_time = -1
        self.processed = False

    @property
    def basename(self) -> str:
        """
        Gets the basename of the image source.
        """
        return os.path.basename(self.full_path)

    @property
    def folder_path(self) -> str:
        """
        Gets the folder path of the image source. The path always ends with a trailing slash.
        """
        return os.path.dirname(self.full_path) + os.path.sep

    @property
    def channels(self):
        """
        Gets the number of channels in the image source.
        """
        return self._raw_image.shape[2]

    @property
    def width(self):
        """
        Gets the width of the image source.
        """
        return self._raw_image.shape[1]

    @property
    def height(self):
        """
        Gets the height of the image source.
        """
        return self._raw_image.shape[0]

    def save(self, path: str):
        """
        Saves the image to a path.
        """
        raw_bgra = cv2.cvtColor(self._raw_image, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(path, raw_bgra)

    def get_image(self) -> QtGui.QImage:
        """
        Returns a QImage of the image.
        """
        return QtGui.QImage(self._raw_image.data, self.width, self.height, QtGui.QImage.Format_RGBA8888)

    def get_pixmap(self) -> QtGui.QPixmap:
        """
        Returns a QPixmap of the image.
        """
        return QtGui.QPixmap(self.get_image())

    def get_pixels_rgb(self) -> np.ndarray:
        """
        Returns the raw image data in RGB format. (No alpha channel)
        """
        return cv2.cvtColor(self._raw_image, cv2.COLOR_RGBA2RGB)

    def get_pixels_rgba(self) -> np.ndarray:
        """
        Returns the raw image data in RGBA format.
        """
        return self._raw_image

    @property
    def faces(self) -> list[Face]:
        """
        Gets the faces in the image.
        """
        return self._faces

    @faces.setter
    def faces(self, value: list[Face]):
        """
        Sets the faces in the image.
        """
        self._faces = value
        for face in self._faces:
            face.image = self
