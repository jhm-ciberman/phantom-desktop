import gzip
import json
import os
import shutil
from typing import Callable

from ..Models import Face, Group, Image, Project
from .ProjectFileBase import ProjectFileBase


class ProjectFileWriter(ProjectFileBase):
    """
    A class that can write a Project to a file. This writer generates non-portable
    project files that can only be opened in the same computer. All the image
    paths are unchanged.
    """

    _files_subfolder = "{project_name}_files"  # This name is inspired by the way that Google Chrome saves its HTML files.

    minify: bool = True
    """Whether to minify the JSON output."""

    gzip: bool = True
    """Whether to gzip the output."""

    portable: bool = None
    """
    Whether to generate a portable project file. A portable project file can be opened
    in any computer and all the image paths are relative to the project file. The images are copied to a
    subfolder named "{project_name}_images" inside the project file folder. Defaults to None, which means
    that the writer will use the same value as the project.is_portable property.
    """

    on_image_copied: Callable[[int, int, Image], None] = None
    """
    A callback that will be called after an image is copied. The callback will receive the
    current image index, the total number of images to copy and the image being copied.
    This callback is only called if portable is True.
    """

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
            "src": self._resolve_src(model.path, portable=self.portable),
            "original_src": self._resolve_src(model.original_path, portable=False),
            "faces": [str(face.id) for face in model.faces],
            "processed": model.processed,
            "hashes": model.hashes,  # dict[str, str] (e.g. {"md5": "1234", "sha1": "5678"})
        }

    def _resolve_src(self, src: str, portable: bool = False) -> str:
        # src could be absolute or relative. For absolute paths, the src looks like:
        # "file:///C:/Users/username/Pictures/image.jpg"
        # for relative paths, the src looks like:
        # "file:./project_files/image.jpg"
        if src is None:
            return None
        if portable:
            return "file:./" + os.path.relpath(src, self._project.dirname)
        return "file:///" + os.path.abspath(src)

    def _encode_project(self, project: Project) -> dict:
        return {
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
            "version": self._current_version,
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

        # Copy the files that are referenced by the project in two passes:
        # First, images that are portable are copied with resolve_conflicts=False.
        # They take precedence because they probably are already in the project folder.
        # Then, images that are not portable are copied with resolve_conflicts=True.
        # This will rename the files if they are already in the project folder.
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
