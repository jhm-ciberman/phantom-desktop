import os
from dataclasses import dataclass
from typing import Any, Sequence
from uuid import UUID, uuid4

import cv2
import numpy as np
from PySide6 import QtCore, QtGui


class Model:
    """
    An abstract model entity that has a unique ID.
    """

    def __init__(self, id: UUID = None) -> None:
        """
        Initializes a new instance of the ProjectEntity class.

        Args:
            id (UUID, optional): The id of the entity. If None, a new id will be generated. Defaults to None.
        """
        self.id = id if id is not None else uuid4()
        self.project = None

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Model):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(frozen=True, repr=True)
class Rect:
    """
    Represents a rectangle.
    """

    x: int
    """The x coordinate of the rectangle."""
    y: int
    """The y coordinate of the rectangle."""
    width: int
    """The width of the rectangle."""
    height: int
    """The height of the rectangle."""

    def to_tuple(self) -> tuple:
        """
        Returns the rectangle as a touple.
        """
        return self.x, self.y, self.width, self.height

    @staticmethod
    def from_tuple(touple: tuple) -> 'Rect':
        """
        Creates a new instance of the Rect class from a touple.
        """
        return Rect(touple[0], touple[1], touple[2], touple[3])


class Face(Model):
    """
    Represents a face in an image. This class is pickleable.

    Attributes:
        aabb (Rect): The axis-aligned bounding box of the face.
        encoding (np.array): The encoding of the face (128 numbers).
        image (Image): The image the face belongs to (None if the face is not part of an image).
        confidence (float): The confidence score of the face.
    """

    def __init__(self, id: UUID = None) -> None:
        """
        Initializes a new instance of the Face class.

        Args:
            id (UUID, optional): The id of the face. If None, a new id will be generated. Defaults to None.
        """
        super().__init__(id)
        self.aabb: 'Rect' = None
        self.encoding: np.ndarray = None  # a flattened list of 128 numbers
        self.image: Image = None
        self.confidence: float = 0.0
        self.group: "Group" = None  # The group the face belongs to, or None if the face is not part of a group.

    def __repr__(self) -> str:
        return "Face(uuid={}, confidence={}, aabb={})".format(self.id, self.confidence, self.aabb)

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


class Group(Model):
    """
    Represents a group of faces.

    Attributes:
        centroid (numpy.ndarray): The centroid of the group.
        faces (list[Face]): The faces in the group.
        name (str): The name of the group.
        main_face (Face): The face that is the most representative of the group.
          By default, the face with the highest confidence score is returned.
        main_face_override (Face): Overrides the main_face property.
        dont_merge_with (set[Group]): A set of groups that should not be merged with this group.
          This is used by the face merger wizard to avoid asking the user twice if they want to merge
          two groups.

    """

    def __init__(self, id: UUID = None) -> None:
        """
        Initializes the Group class.

        Args:
            id (UUID): The ID of the group. If None, a new ID will be generated. Defaults to None.
        """
        super().__init__(id)
        self.centroid: np.ndarray = None  # a flattened list of 128 numbers
        self._faces: list[Face] = []
        self.main_face_override: Face = None
        self.name: str = None
        self.dont_merge_with: set[Group] = set()

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
    def faces(self) -> Sequence[Face]:
        """
        Gets the faces in the group.
        """
        return self._faces

    def count_unique_images(self) -> int:
        """
        Gets the number of unique images the group is part of.
        """
        return len(set([face.image for face in self._faces]))

    def add_face(self, face: Face) -> None:
        """
        Adds a face to the group.
        """
        if face.group is not None:
            raise Exception("The face is already part of a group.")

        self._faces.append(face)
        face.group = self

    def remove_face(self, face: Face) -> None:
        """
        Removes a face from the group.
        """
        if self.main_face_override == face:
            self.main_face_override = None

        self._faces.remove(face)
        face.group = None

    def clear_faces(self) -> None:
        """
        Removes all faces from the group.
        """
        for face in self._faces:
            face.group = None
        self._faces.clear()
        self.main_face_override = None
        self.centroid = None

    def merge(self, other: "Group", recompute_centroid: bool = True) -> None:
        """
        Merges another group into this group.

        Args:
            other (Group): The other group.
            recompute_centroid (bool): If True, the centroid will be recomputed. Defaults to True.
        """
        # Combine faces
        self._faces.extend(other.faces)

        # Copy name if target group has no name
        if not self.name:
            self.name = other.name

        # Copy the main face override if target group has no main face override
        if not self.main_face_override:
            self.main_face_override = other.main_face_override

        # Recompute centroid
        if recompute_centroid:
            self.recompute_centroid()

    def recompute_centroid(self) -> None:
        """
        Recomputes the centroid of the group.
        """
        if not self._faces:
            return

        if (len(self._faces) == 1):  # Early exit if there is only one face
            self.centroid = self._faces[0].encoding
            return

        # Compute the centroid
        self.centroid = np.mean([face.encoding for face in self._faces], axis=0)


class Image(Model):
    """
    The Image class is the main Phantom Desktop image model.
    It represents an image loaded into memory. This class
    holds metadata about the image, and provides methods for accessing the raw color
    bytes of the image. The raw color bytes are stored in RGBA format, with each
    channel being a uint8 array.

    Attributes:
        raw_image (cv2.Mat): The raw image data in RGBA format.
        faces (list[Face]): The faces in the image.
        faces_time (int): The time it took to process the faces in nanoseconds.
        processed (bool): Whether or not the image has been processed by the face detector.
        original_full_path (str): The original full path of the image.
    """

    def __init__(self, path: str, id: UUID = None, load: bool = True) -> None:
        """
        Initializes the Image class.

        Args:
            id (UUID): The ID of the image. If None, a new ID will be generated. Defaults to None.
            path (str): The path to the image source (can be relative or absolute).
            load (bool): Whether or not to load the image into memory. Defaults to True.
        """
        super().__init__(id)
        self._full_path = os.path.abspath(path)
        self._is_loaded = False
        self._raw_image = None
        self._faces: "list[Face]" = []
        self.processed = False
        self.original_full_path = self._full_path

        if load:
            self.load()

    def load(self) -> None:
        """
        Loads the image into memory.
        """
        if not self._is_loaded:
            raw_image = cv2.imread(self._full_path, cv2.IMREAD_UNCHANGED)
            if raw_image is None:
                raise Exception(f"Failed to load image: {self._full_path}")
            self._raw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGBA)
            self._is_loaded = True

    def unload(self) -> None:
        """
        Unloads the image from memory.
        """
        self._raw_image = None
        self._is_loaded = False

    @property
    def full_path(self) -> str:
        """
        Gets the full path of the image source.
        """
        return self._full_path

    @property
    def basename(self) -> str:
        """
        Gets the basename of the image source.
        """
        return os.path.basename(self._full_path)

    @property
    def folder_path(self) -> str:
        """
        Gets the folder path of the image source. The path always ends with a trailing slash.
        """
        return os.path.dirname(self._full_path) + os.path.sep

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

    @property
    def original_basename(self) -> str:
        """
        Gets the basename of the original image source.
        """
        return os.path.basename(self.original_full_path)

    @property
    def original_folder_path(self) -> str:
        """
        Gets the folder path of the original image source. The path always ends with a trailing slash.
        """
        return os.path.dirname(self.original_full_path) + os.path.sep

    @property
    def is_loaded(self) -> bool:
        """
        Gets whether or not the image is loaded into memory.
        """
        return self._is_loaded

    def _assert_loaded(self) -> None:
        if not self.is_loaded:
            raise Exception("The image is not loaded. Call the load() method to load the image before accessing it.")

    def save(self, path: str):
        """
        Saves the image to a path.
        """
        self._assert_loaded()
        raw_bgra = cv2.cvtColor(self._raw_image, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(path, raw_bgra)

    def get_image(self) -> QtGui.QImage:
        """
        Returns a QImage of the image.
        """
        self._assert_loaded()
        return QtGui.QImage(self._raw_image.data, self.width, self.height, QtGui.QImage.Format_RGBA8888)

    def get_pixmap(self) -> QtGui.QPixmap:
        """
        Returns a QPixmap of the image.
        """
        self._assert_loaded()
        return QtGui.QPixmap(self.get_image())

    def get_pixels_rgb(self) -> np.ndarray:
        """
        Returns the raw image data in RGB format. (No alpha channel)
        """
        self._assert_loaded()
        return cv2.cvtColor(self._raw_image, cv2.COLOR_RGBA2RGB)

    def get_pixels_rgba(self) -> np.ndarray:
        """
        Returns the raw image data in RGBA format.
        """
        self._assert_loaded()
        return self._raw_image

    @property
    def faces(self) -> list[Face]:
        """
        Gets the faces in the image.
        """
        return self._faces

    def clear_faces(self) -> None:
        """
        Removes all faces from the image.
        """
        self._faces.clear()

    def add_face(self, face: Face):
        """
        Adds a face to the image.
        """
        self._faces.append(face)
        face.image = self

    def remove_face(self, face: Face):
        """
        Removes a face from the image.
        """
        self._faces.remove(face)
        face.image = None

    def read_file_bytes(self) -> bytes:
        """
        Returns the raw bytes of the image file as read from disk. (Including metadata)
        This is different from get_pixels_rgba() which returns the raw image data in RGBA format.
        """
        with open(self.full_path, "rb") as file:
            return file.read()


class Project:
    """
    Represents a project file.
    """

    def __init__(self, file_path: str = None):
        """
        Initializes the Project class.

        Args:
            file_path (str): The path to the project file.
        """
        super().__init__()
        self.file_path = file_path
        self._images: "list[Image]" = []
        self._images_ids: "dict[UUID, Image]" = {}  # Enables O(1) lookup by ID
        self._groups: "list[Group]" = []
        self._groups_ids: "dict[UUID, Group]" = {}  # Enables O(1) lookup by ID

        if file_path is not None:
            self.load(file_path)

    @property
    def images(self) -> Sequence[Image]:
        """Gets the images in the project."""
        return self._images

    def add_image(self, image: Image):
        """Adds an image to the project."""
        self._images.append(image)
        self._images_ids[image.id] = image

    def remove_image(self, image: Image):
        """Removes an image from the project."""
        self._images.remove(image)
        del self._images_ids[image.id]
        if image.faces:
            for face in image.faces:
                self.remove_face_from_groups(face)

    def has_image(self, image: Image) -> bool:
        """Returns True if the project contains the image."""
        return image.id in self._images_ids

    def remove_face_from_groups(self, face: Face):
        """Removes a face from all groups."""
        for group in self._groups:
            if face in group.faces:
                group.remove_face(face)

    def add_face_to_best_group(self, face: Face):
        """Adds a face to the best group."""
        from .GroupFaces.ClusteringService import find_best_group
        group = find_best_group(face, self._groups)
        if group is None:
            group = Group()
            self.add_group(group)
        group.add_face(face)
        group.recompute_centroid()

    @property
    def groups(self) -> Sequence[Group]:
        """Gets the groups in the project."""
        return self._groups

    def add_group(self, group: Group):
        """Adds a group to the project."""
        self._groups.append(group)
        self._groups_ids[group.id] = group

    def remove_group(self, group: Group):
        """Removes a group from the project."""
        self._groups.remove(group)
        del self._groups_ids[group.id]

    def has_group(self, group: Group) -> bool:
        """Returns True if the project contains the group."""
        return group.id in self._groups_ids

    def get_faces(self) -> Sequence[Face]:
        """Gets all the faces in the project."""
        faces = []
        for image in self._images:
            faces.extend(image.faces)
        return faces

    def get_faces_without_group(self) -> Sequence[Face]:
        """Gets all the faces in the project that are not in a group."""
        faces = []
        for image in self._images:
            for face in image.faces:
                if not face.group:
                    faces.append(face)
        return faces

    def regroup_faces(self):
        """Regroups all the faces in the project."""
        from .GroupFaces.ClusteringService import cluster
        self._groups = []
        self._groups_ids = {}
        for group in cluster(self.get_faces()):
            self.add_group(group)

    def save(self, file_path: str = None):
        """Saves the project to a file."""
        if file_path is not None:
            self.file_path = file_path
        if self.file_path is None:
            raise Exception("The project file path is not set.")
        from .ProjectFile import ProjectFileWriter  # Avoid circular import
        ProjectFileWriter().write(self.file_path, self)

    def load(self, file_path: str = None):
        """Loads the project from a file."""
        if file_path is not None:
            self.file_path = file_path
        if self.file_path is None:
            raise Exception("The project file path is not set.")
        from .ProjectFile import ProjectFileReader  # Avoid circular import
        ProjectFileReader().read(self.file_path, self)

    @property
    def is_empty(self) -> bool:
        """Returns True if the project is empty."""
        return len(self._images) == 0
