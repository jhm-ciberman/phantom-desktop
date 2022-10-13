import base64
import gzip
import json
from typing import Any, Callable
from uuid import UUID

import numpy as np

from .Models import Face, Group, Image, Model, Project, Rect


class ProjectBufferSection:
    """
    A buffers that can store numpy arrays with a given dtype
    A buffers is stored in the JSON project file as a binary blob encoded as base64 string.
    """

    def __init__(self, dtype: str, stride: int) -> None:
        """
        Initializes a new instance of the ProjectBufferSection class.

        Args:
            dtype (str): The dtype of the arrays that will be stored in the buffer.
            stride (int): The length of the arrays that will be stored in the buffer.
        """
        self._data: list[np.ndarray] = []
        self._dtype = dtype
        self._stride = stride

    def store(self, array: np.ndarray) -> int:
        """
        Stores the specified array in the section
        and returns it's index.

        Args:
            array (np.array): The array to store.

        Returns:
            int: The index of the data.
        """
        if array is None:
            return -1

        if array.dtype != self._dtype:
            raise ValueError(f"Expected dtype {self._dtype.str}, got {array.dtype}")

        if array.size != self._stride:
            raise ValueError(f"Expected array of size {self._stride}, got {array.size}")

        index = len(self._data)
        self._data.append(array)
        return index

    def load(self, index: int) -> np.array:
        """
        Gets the data at the specified index.

        Args:
            index (int): The index.

        Returns:
            np.array: The data.
        """
        return self._data[index] if index >= 0 else None

    def to_json(self) -> dict[str, Any]:
        """
        Returns the JSON representation of the object.

        Returns:
            dict[str, Any]: A JSON representation of the object
        """
        return {
            "dtype": self._dtype,
            "stride": self._stride,
            "data": base64.b64encode(
                np.concatenate(self._data).astype(self._dtype).tobytes()
            ).decode("utf-8"),
        }

    def from_json(self, json: dict[str, Any]) -> None:
        """
        Hydrates a new ProjectBufferSection object from the specified JSON object.

        Args:
            json (dict[str, Any]): The JSON object.
        """
        self._dtype = json["dtype"]  # TODO: Check if dtype is valid
        self._stride = json["stride"]
        self._data = np.frombuffer(
            base64.b64decode(json["data"]), dtype=self._dtype
        ).reshape((-1, self._stride))
        self._current_offset = self._data.size


class ProjectModelsSection:
    """
    A an abstract class that represents a section that can store Models inside the Project file.
    """

    def __init__(self, obj_cls: type) -> None:
        """
        Initialize a new section.

        Args:
            project (Project): The project that owns the section.
            obj_cls (type): The type of the objects that can be stored in the section.
        """
        self._data: dict[UUID, object] = {}
        self._obj_cls = obj_cls

    def add(self, obj: Model) -> None:
        """
        Stores the specified object in the section.

        Args:
            id (UUID): The id of the object.
            obj: The object to store.
        """
        if obj.id in self._data:
            return
        if not isinstance(obj, self._obj_cls):
            raise ValueError(
                f"Expected object of type {self._obj_cls}, got {type(obj)}"
            )
        self._data[obj.id] = obj

    def get(self, id: UUID) -> Model:
        """
        Gets the object with the specified id.

        Args:
            id (UUID): The id of the object.

        Returns:
            Model: The object.
        """
        return self._data[id] if id in self._data else None

    @property
    def models(self) -> list[Model]:
        """
        Gets the data stored in the section.

        Returns:
            list[object]: The data.
        """
        return self._data.values()

    def from_json(self, data: list[dict[str, Any]], decode_fn: Callable) -> None:
        """
        Loads the data from the specified JSON object.

        Args:
            data (list[dict[str, Any]]): The JSON object.
            decode_fn (callable): A function that can decode a JSON object into a Model object.
        """
        for obj in data:
            self.add(decode_fn(obj))

    def to_json(self, encode_fn: Callable) -> list[dict[str, Any]]:
        """
        Returns the JSON representation of the object.

        Returns:
            list[dict[str, Any]]: A JSON representation of the object.
        """
        return [encode_fn(obj) for obj in self._data.values()]

    def resolve_relations(self, data: list[dict[str, Any]], resolve_fn: Callable) -> None:
        """
        Resolves the relations between the objects in the section.

        Args:
            data (list[dict[str, Any]]): The JSON object.
            resolve_fn (callable): A function that can resolve the relations of a JSON object.
        """
        for obj, data in zip(self._data.values(), data):
            resolve_fn(obj, data)


class ProjectFileBase:
    """
    An abstract base class for ProjectFileWriter and ProjectFileReader.
    """

    _current_version = 1

    _client_name = "Phantom Desktop"

    _client_version = "0.0.0"

    def __init__(self) -> None:
        """
        Initializes the ProjectFileBase class.
        """
        # Buffer sections:
        self._encodings_buff = ProjectBufferSection("float64", 128)  # 128 doubles per encoding
        # self._shapes_buff = ProjectBufferSection("int32", 68 * 2)  # 68 points per shape, 2 ints per point

        # Model sections:
        self._images = ProjectModelsSection(Image)
        self._faces = ProjectModelsSection(Face)
        self._groups = ProjectModelsSection(Group)


class ProjectFileWriter(ProjectFileBase):
    """
    A class that can write a Project to a file.
    """

    def __init__(self, minify: bool = True, gzip: bool = True) -> None:
        """
        Initializes the ProjectFileWriter class.

        Args:
            minify (bool, optional): Whether to minify the JSON output. Defaults to True.
            gzip (bool, optional): Whether to gzip the output. Defaults to True.
        """
        super().__init__()
        self._minify = minify
        self._gzip = gzip

    def _visit_face(self, face: Face):
        self._faces.add(face)

    def _visit_group(self, group: Face):
        self._groups.add(group)
        for face in group.faces:
            self._visit_face(face)
        if group.main_face_override:
            self._visit_face(group.main_face_override)

    def _visit_image(self, image: Image):
        self._images.add(image)
        for face in image.faces:
            self._visit_face(face)

    def _visit_project(self, project: Project):
        for image in project.images:
            self._visit_image(image)
        for group in project.groups:
            self._visit_group(group)

    def _encode_face(self, model: Face) -> dict:
        return {
            "id": str(model.id),
            "aabb": model.aabb.to_tuple(),
            "encoding": self._encodings_buff.store(model.encoding),
            "confidence": model.confidence
        }

    def _encode_group(self, model: Group) -> dict:
        return {
            "id": str(model.id),
            "name": model.name,
            "faces": [str(face.id) for face in model.faces],
            "main_face_override": str(model.main_face_override.id) if model.main_face_override else None,
            "centroid": self._encodings_buff.store(model.centroid),
            "dont_merge_with": [str(group.id) for group in model.dont_merge_with],
        }

    def _encode_image(self, model: Image) -> dict:
        return {
            "id": str(model.id),
            "src": model.full_path,
            "original_src": model.original_full_path,
            "faces": [str(face.id) for face in model.faces],
            "processed": model.processed,
        }

    def _encode_project(self, project: Project) -> dict:
        return {
            "header": {
                "version": self._current_version,
                "client_name": self._client_name,
                "client_version": self._client_version,
            },
            "images": self._images.to_json(self._encode_image),
            "groups": self._groups.to_json(self._encode_group),
            "faces": self._faces.to_json(self._encode_face),
            "buffers": {
                "encodings": self._encodings_buff.to_json(),
            },
        }

    def write(self, path: str, project: Project) -> None:
        """
        Saves the project to the specified path.

        Args:
            path (str): The path to the project.
            project (Project): The project to save.
        """
        self._visit_project(project)
        data = self._encode_project(project)
        indent = 4 if not self._minify else None

        project.file_path = path

        if self._gzip:
            with gzip.open(path, "wt") as f:
                json.dump(data, f, indent=indent)
        else:
            with open(path, "w") as f:
                json.dump(data, f, indent=indent)


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

    def __init__(self) -> None:
        """
        Initializes the ProjectFileReader class.
        """
        super().__init__()

    def _decode_face(self, data: dict) -> Face:
        face = Face(data["id"])
        face.aabb = Rect.from_tuple(data["aabb"])
        face.confidence = data.get("confidence")
        return face

    def _decode_group(self, data: dict) -> Group:
        group = Group(data["id"])
        group.name = data.get("name", "")
        return group

    def _decode_image(self, data: dict) -> Image:
        image = Image(data["src"], data["id"])
        image.original_full_path = data.get("original_src", image.full_path)
        image.processed = data.get("processed", False)
        return image

    def _resolve_face(self, face: Face, data: dict):
        face.encoding = self._encodings_buff.load(data["encoding"])
        pass

    def _resolve_group(self, group: Group, data: dict):
        group.main_face_override = self._faces.get(data.get("main_face_override"))
        for face in [self._faces.get(id) for id in data.get("faces", [])]:
            group.add_face(face)
        group.centroid = self._encodings_buff.load(data.get("centroid"))
        for other_group in data.get("dont_merge_with", []):
            group.dont_merge_with.append(self._groups.get(other_group))

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
        version = json["header"]["version"]
        if version == 1:
            return json
        raise UnsuportedFileVersionException(version, self._current_version, "File version is not supported.")

    def _is_gzip(self, file) -> bool:
        file.seek(0)
        return file.read(2) == b"\x1f\x8b"  # gzip magic number

    def _is_json(self, file) -> bool:
        file.seek(0)
        return file.read(1) == b"{"

    def _load_json(self, file) -> dict[str, Any]:
        file.seek(0)
        return json.load(file)

    def _load_gzip(self, file) -> dict[str, Any]:
        file.seek(0)
        with gzip.open(file, "rt") as gzip_file:
            return json.load(gzip_file)

    def _load(self, file) -> dict[str, Any]:
        if self._is_gzip(file):
            return self._load_gzip(file)
        elif self._is_json(file):
            return self._load_json(file)
        raise Exception("File is not a valid project file.")

    def read(self, path: str, project: Project = None) -> Project:
        """
        Loads a project from the specified path.

        Args:
            path (str): The path to the project.
            project (Project, optional): The project to load the data into.
                If None, a new project will be created. Defaults to None.

        Returns:
            Project: The project.
        """
        with open(path, "rb") as file:
            data = self._load(file)

        data = self._migrate(data)

        version = data["header"]["version"]
        if version != self._current_version:
            raise UnsuportedFileVersionException(version, self._current_version, "File version is not supported.")

        # First, load the buffers:
        buffers = data["buffers"]
        self._encodings_buff.from_json(buffers["encodings"])

        # Then, load the models without relations:
        self._images.from_json(data["images"], self._decode_image)
        self._faces.from_json(data["faces"], self._decode_face)
        self._groups.from_json(data["groups"], self._decode_group)

        # Now that all models are loaded, resolve the relations:
        self._images.resolve_relations(data["images"], self._resolve_image)
        self._faces.resolve_relations(data["faces"], self._resolve_face)
        self._groups.resolve_relations(data["groups"], self._resolve_group)

        project = project or Project()
        project.file_path = path
        for image in self._images.models:
            project.add_image(image)
        for group in self._groups.models:
            project.add_group(group)
        return project
