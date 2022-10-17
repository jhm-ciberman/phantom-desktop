import base64
from typing import Any, Callable
from uuid import UUID

import numpy as np

from ..Models import Face, Group, Image, Model


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
            "count": len(self._data),
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

    def __iter__(self):
        return iter(self._data.values())

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]


class ProjectFileBase:
    """
    An abstract base class for ProjectFileWriter and ProjectFileReader.
    """
    from ..Application import Application

    _current_version = 1

    _client_name = "Phantom Desktop"

    _client_version = Application.applicationVersion()

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
