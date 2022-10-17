import base64
from functools import partial
import gzip
import json
import os
import shutil
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
    A class that can write a Project to a file. This writer generates non-portable
    project files that can only be opened in the same computer. All the image
    paths are unchanged.

    Attributes:
        minify (bool): Whether to minify the JSON output. Defaults to True.
        gzip (bool): Whether to gzip the output. Defaults to True.
        portable (bool): Whether to generate a portable project file. A portable
            project file can be opened in any computer and all the image paths
            are relative to the project file. The images are copied to a subfolder
            named "{project_name}_images" inside the project file folder. Defaults
            to None, which means that the writer will use the same value as the
            project.is_portable property.
        on_image_copied (Callable[[int, int, Image], None], optional): A callback that will be called
            after an image is copied. The callback will receive the current image index, the total number
            of images to copy and the image being copied. This callback is only called if portable is True.
            Defaults to None.
    """

    _files_subfolder = "{project_name}_files"  # This name is inspired by the way that Google Chrome saves its HTML files.

    def __init__(
            self, project: Project, minify: bool = True, gzip: bool = True, portable: bool = None,
            on_image_copied: Callable[[int, int, Image], None] = None) -> None:
        """
        Initializes the ProjectFileWriter class.

        Args:
            project (Project): The project to write.
            minify (bool, optional): Whether to minify the JSON output. Defaults to True.
            gzip (bool, optional): Whether to gzip the output. Defaults to True.
            portable (bool, optional): Whether to generate a portable project file. A portable
                project file can be opened in any computer and all the image paths
                are relative to the project file. The images are copied to a subfolder
                named "{project_name}_images" inside the project file folder. Defaults
                to None, which means that the writer will use the same value as the
                project.is_portable property.
            on_image_copied (Callable[[int, int, Image], None], optional): A callback that will be called
                after an image is copied. The callback will receive the current image index, the total number
                of images to copy and the image being copied. This callback is only called if portable is True.
                Defaults to None.
        """
        super().__init__()
        self._project = project
        self.minify = minify
        self.gzip = gzip
        self.portable = portable if portable is not None else project.is_portable
        self.on_image_copied = on_image_copied or (lambda index, total, image: None)

    def _visit_face(self, face: Face):
        self._faces.add(face)

    def _visit_group(self, group: Group):
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
            "src": self._resolve_src(model.path),
            "original_src": model.original_path,
            "faces": [str(face.id) for face in model.faces],
            "processed": model.processed,
            "hashes": model.hashes,  # dict[str, str] (e.g. {"md5": "1234", "sha1": "5678"})
        }

    def _resolve_src(self, src: str) -> str:
        # src could be absolute or relative. For absolute paths, the src looks like:
        # "file:///C:/Users/username/Pictures/image.jpg"
        # for relative paths, the src looks like:
        # "file:./project_files/image.jpg"
        if self.portable:
            return "file:./" + os.path.relpath(src, self._project.dirname)
        return "file:///" + os.path.abspath(src)

    def _encode_project(self, project: Project) -> dict:
        return {
            "version": self._current_version,
            "client_name": self._client_name,
            "client_version": self._client_version,
            "files_dir": project.files_dir,
        }

    def _encode_buffers(self) -> dict:
        return {
            "encodings": self._encodings_buff.to_json(),
        }

    def _encode_file(self, project: Project) -> dict:
        return {
            "project": self._encode_project(project),
            "images": self._images.to_json(self._encode_image),
            "faces": self._faces.to_json(self._encode_face),
            "groups": self._groups.to_json(self._encode_group),
            "buffers": self._encode_buffers(),
        }

    def write(self, path: str) -> None:
        """
        Saves the project to the specified path.

        Args:
            path (str): The path to the project.
            project (Project): The project to save.
        """
        self._project.path = path

        if self.portable:
            self._copy_portable_files(path)

        self._visit_project(self._project)
        data = self._encode_file(self._project)
        indent = 4 if not self.minify else None

        if self.gzip:
            with gzip.open(path, "wt") as f:
                json.dump(data, f, indent=indent)
        else:
            with open(path, "w") as f:
                json.dump(data, f, indent=indent)

    def _file_is_aleady_in_folder(self, file_path: str, folder_path: str) -> bool:
        """
        Returns True if the file is contained in the folder.
        For example, if the file is "C:/Users/username/Pictures/image.jpg"
        and the folder is "C:/Users/username", this method will return True.
        If the file is "C:/Users/username/Pictures/image.jpg"
        and the folder is "F:/backup", this method will return False.

        Args:
            file_path (str): The file path.
            folder_path (str): The folder path.

        Returns:
            bool: True if the file is contained in the folder.
        """
        file_path = os.path.normpath(os.path.abspath(file_path))
        folder_path = os.path.normpath(os.path.abspath(folder_path))
        return file_path.startswith(folder_path)

    def _copy_portable_files(self, path: str) -> None:
        """
        Copies the images to a subfolder named "{project_name}_images" inside the project file folder.

        Args:
            path (str): The path to the project file.
        """
        project_name = self._project.name
        self._project.files_dir = self._files_subfolder.format(project_name=project_name)
        dir_path = os.path.join(os.path.dirname(path), self._project.files_dir)

        os.makedirs(dir_path, exist_ok=True)

        # copy the files that are referenced by the project in two passes:
        # First, images that are portable are copied with resolve_conflicts=False. They take precedence because they probably are already
        # in the project folder. Then, images that are not portable are copied with resolve_conflicts=True. This will rename the files
        # if they are already in the project folder.
        total = len(self._project.images)
        portable_images: list[Image] = []
        nonportable_images: list[Image] = []
        for image in self._project.images:
            if self._file_is_aleady_in_folder(image.path, dir_path):
                portable_images.append(image)
            else:
                nonportable_images.append(image)

        for index, image in enumerate(portable_images):
            self._copy_image(image, dir_path, resolve_conflicts=False)
            self.on_image_copied(index, total, image)

        start_index = len(portable_images)
        for index, image in enumerate(nonportable_images):
            self._copy_image(image, dir_path, resolve_conflicts=True)
            self.on_image_copied(index + start_index, total, image)

    def _copy_image(self, image: Image, dir_path: str, resolve_conflicts: bool) -> None:
        """
        Copies the specified image to the specified directory. The image will be renamed if a file with the same name
        already exists in the directory.

        Args:
            image (Image): The image to copy.
            dir_path (str): The directory to copy the image to.
            resolve_conflicts (bool): If True, the image will be renamed if a file
                with the same name already exists in the directory.
        """
        src_path = image.path
        dest_path = os.path.join(dir_path, os.path.basename(image.path))

        if resolve_conflicts:
            dest_path = self._resolve_conflicts(dest_path)

        if src_path != dest_path:
            shutil.copy2(src_path, dest_path)
            image.path = dest_path

    def _resolve_conflicts(self, file_path: str) -> str:
        """
        Returns the absolute path of the specified file name resolving name conflicts if necessary.
        If the file already exists, a number will be appended to the file name to make it unique.
        E.g.: "image.jpg" -> "image_1.jpg", "image_2.jpg", etc.

        Args:
            file_path (str): The file path.

        Returns:
            str: The absolute path of the file.
        """
        file_name = os.path.basename(file_path)
        dir = os.path.dirname(file_path)
        file_name_no_ext, ext = os.path.splitext(file_name)
        i = 1
        while os.path.exists(os.path.join(dir, file_name)):
            file_name = f"{file_name_no_ext}_{i}{ext}"
            i += 1
        return os.path.join(dir, file_name)


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
        self._on_progress = on_progress or (lambda i, t, img: None)
        self._on_image_error = on_image_error or (lambda e, img: None)

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
        version = json["project"]["version"]
        if version == 1:
            return json
        # In the future, add more elif statements here to migrate from version 2 to 3, from 3 to 4, etc.
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

        self._assert_version_supported(data["project"]["version"])

        # First, Decode the basic project data
        project = self._decode_project(data["project"], path)

        # Load the buffers:
        buffers = data["buffers"]
        self._encodings_buff.from_json(buffers["encodings"])

        # Then, load the models without relations:
        self._images.from_json(data["images"], partial(self._decode_image, project))
        self._faces.from_json(data["faces"], partial(self._decode_face, project))
        self._groups.from_json(data["groups"], partial(self._decode_group, project))

        # Now that all models are loaded, resolve the relations:
        self._images.resolve_relations(data["images"], self._resolve_image)
        self._faces.resolve_relations(data["faces"], self._resolve_face)
        self._groups.resolve_relations(data["groups"], self._resolve_group)

        # Now, load the images into memory and return the project:
        for i, image in enumerate(self._images):
            self._load_image(image, project, i)
            project.add_image(image)

        for group in self._groups.models:
            project.add_group(group)

        return project

    def _assert_version_supported(self, version: int):
        if version != self._current_version:
            raise UnsuportedFileVersionException(version, self._current_version, "File version is not supported.")

    def _load_image(self, image: Image, project: Project, index: int):
        try:
            image.load(project.files_dir)
        except Exception as e:
            if not self._on_image_error(e, image):
                raise e
        self._on_progress(index, len(self._images), image)
