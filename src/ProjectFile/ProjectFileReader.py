import gzip
from io import BufferedReader
import json
import os
from functools import partial
from typing import Any, Callable

from ..Models import Face, Group, Image, Project, Rect
from .ProjectFileBase import ProjectFileBase


class UnsuportedFileVersionException(Exception):
    """
    Exception that is thrown when the file version is not supported.
    """

    def __init__(self, file_version: int, current_version: int, message: str):
        """
        Initializes a new instance of the UnsuportedFileVersionException class.

        Args:
            file_version (int): The version of the file that was read.
            current_version (int): The current version of the file format that is supported by the reader.
            message (str): The message.
        """
        super().__init__(message)
        self.file_version = file_version
        self.current_version = current_version


class ProjectFileReader(ProjectFileBase):
    """
    A class that can read a Project from a file.
    """

    on_progress: Callable[[int, int, Image], None] = lambda index, total, image: None
    """
    A callback that is called when an image is loaded (or failed to load).
    The callback receives the image index, the total number of images,
    and the image that was loaded.
    """

    on_image_error: Callable[[Exception, Image], None] = lambda exception, image: None
    """
    A callback that is called when an image fails to load.
    The callback receives the exception and the image that failed to load.
    The callback can return True to ignore the error and continue loading the project,
    or False to stop loading the project. The on_image_error callback is called
    before the on_progress callback.
    """

    def __init__(
            self, on_progress: Callable[[int, int, Image], None] = None,
            on_image_error: Callable[[Exception, Image], bool] = None) -> None:
        """
        Initializes the ProjectFileReader class.

        Args:
            on_progress (Callable[[int, int, Image], None], optional): A callback that
                is called when an image is loaded (or failed to load). The callback
                image index, the total number of images, and the image that was loaded.
            on_image_error (Callable[[Exception, Image], None], optional): A callback
                that is called when an image fails to load. The callback receives the
                exception and the image that failed to load. The callback can return
                True to ignore the error and continue loading the project, or False
                to stop loading the project. The on_image_error callback is called
                before the on_progress callback.
        """
        super().__init__()
        self.on_progress = on_progress or (lambda i, t, img: None)
        self.on_image_error = on_image_error or (lambda e, img: None)

    def _decode_face(self, project: Project, data: dict) -> Face:
        face = Face(data["id"])
        face.aabb = Rect.from_tuple(data["aabb"])
        face.confidence = data.get("confidence")
        return face

    def _decode_group(self, project: Project, data: dict) -> Group:
        group = Group(data["id"])
        group.name = data.get("name", "")
        return group

    def _decode_image(self, project: Project, data: dict) -> Image:
        path = self._resolve_src(data["src"], project.dirname)
        image = Image(path, data["id"])  # Don't load the image yet
        image.original_path = data.get("original_src", image.path)
        image.processed = data.get("processed", False)
        image.hashes = data.get("hashes", {})
        return image

    def _resolve_src(self, src: str, base_relative_dir: str) -> str:
        # src could be absolute or relative. For absolute paths, the src looks like:
        # "file:///C:/Users/username/Pictures/image.jpg"
        # for relative paths, the src looks like:
        # "file:./project_files/image.jpg"
        if src.startswith("file:///"):
            return src[8:]
        elif src.startswith("file:"):
            return os.path.join(base_relative_dir, src[5:])
        else:
            return src  # This is not in the spec, but support it anyway

    def _decode_project(self, data: dict, path: str) -> Project:
        files_dir = data.get("files_dir", None)
        if files_dir:
            files_dir = os.path.join(os.path.dirname(path), files_dir)
        project = Project()
        project.files_dir = files_dir
        project.path = path
        return project

    def _resolve_face(self, face: Face, data: dict):
        face.encoding = self._encodings_buff.load(data["encoding"])
        pass

    def _resolve_group(self, group: Group, data: dict):
        group.main_face_override = self._faces.get(data.get("main_face_override"))
        for face in [self._faces.get(id) for id in data.get("faces", [])]:
            group.add_face(face)
        group.centroid = self._encodings_buff.load(data.get("centroid"))
        for other_group in data.get("dont_merge_with", []):
            group.dont_merge_with.add(self._groups.get(other_group))

    def _resolve_image(self, image: Image, data: dict):
        for face in [self._faces.get(id) for id in data.get("faces", [])]:
            image.add_face(face)

    def _migrate(self, json: dict[str, Any]) -> dict[str, Any]:
        """
        Migrates the specified json to the current version.

        Args:
            json (dict[str, Any]): The json to migrate.

        Returns:
            dict[str, Any]: The migrated json.
        """
        version = json["version"]
        if version == 1:
            return json
        # In the future, add more elif statements here to migrate from version 2 to 3, from 3 to 4, etc.
        raise UnsuportedFileVersionException(version, self._current_version, "File version is not supported.")

    def _is_gzip(self, file: BufferedReader) -> bool:
        file.seek(0)
        return file.read(2) == b"\x1f\x8b"  # gzip magic number

    def _is_json(self, file: BufferedReader) -> bool:
        file.seek(0)
        return file.read(1) == b"{"

    def _load_json(self, file: BufferedReader) -> dict[str, Any]:
        file.seek(0)
        return json.load(file)

    def _load_gzip(self, file: BufferedReader) -> dict[str, Any]:
        file.seek(0)
        with gzip.open(file, "rt") as gzip_file:
            return json.load(gzip_file)

    def _load(self, file: BufferedReader) -> dict[str, Any]:
        if self._is_gzip(file):
            return self._load_gzip(file)
        elif self._is_json(file):
            return self._load_json(file)
        raise Exception("File is not a valid project file.")

    def read(self, path: str) -> Project:
        """
        Loads a project from the specified path.

        Args:
            path (str): The path to the project.

        Returns:
            Project: The loaded project.
        """
        with open(path, "rb") as file:
            data = self._load(file)

        data = self._migrate(data)

        self._assert_version_supported(data["version"])

        # First, Decode the basic project data
        project = self._decode_project(data["project"], path)

        # Load the buffers:
        buffers = data.get("buffers", {})
        if "encodings" in buffers:
            self._encodings_buff.from_json(buffers["encodings"])

        # Then, load the models without relations:
        self._images.from_json(data.get("images", []), partial(self._decode_image, project))
        self._faces.from_json(data.get("faces", []), partial(self._decode_face, project))
        self._groups.from_json(data.get("groups", []), partial(self._decode_group, project))

        # Now that all models are loaded, resolve the relations:
        self._images.resolve_relations(data["images"], self._resolve_image)
        self._faces.resolve_relations(data["faces"], self._resolve_face)
        self._groups.resolve_relations(data["groups"], self._resolve_group)

        # Now, load the images into memory and return the project:
        for i, image in enumerate(self._images):
            self._load_image(image, i, project)

        for group in self._groups.models:
            project.add_group(group)

        return project

    def _assert_version_supported(self, version: int):
        if version != self._current_version:
            raise UnsuportedFileVersionException(version, self._current_version, "File version is not supported.")

    def _load_image(self, image: Image, index: int, project: Project):
        try:
            image.load()
            project.add_image(image)
        except Exception as e:
            if not self.on_image_error(e, image):
                raise e
        self.on_progress(index, len(self._images), image)
