import os
from typing import Any

from PIL import Image as PILImage
from PIL.ExifTags import TAGS

from ..Application import Application
from ..l10n import __
from ..Models import Face, Image, Project
from ..Widgets.PropertiesTable import PropertiesTable


class InfoProvider:
    """
    Base class for objects that provide information about a selected object.
    """

    def populate(self, table: "PropertiesTable"):
        """
        Populate the properties table with information about the selected object.
        """
        raise NotImplementedError()


class ImageInfoProvider(InfoProvider):
    """
    Provides information an image.
    """

    def __init__(self, image: list[Image]):
        self._image = image

    def populate(self, table: PropertiesTable):
        """
        Populate the properties table with information about the selected object.
        """
        image = self._image
        pilImage = PILImage.open(image.path)
        self._printBasicInformation(table, image, pilImage)
        self._printHashes(table, image)
        self._printExif(table, pilImage)
        self._printFaceDetection(table, image)

    def _printBasicInformation(self, table: PropertiesTable, image: Image, pilImage: PILImage):
        table.addHeader(__("Basic Information"))
        fileSize = os.path.getsize(image.path)
        path = image.path
        original_path = image.original_path

        table.addRow(__("Filename"), os.path.basename(path))
        table.addRow(__("Folder"), os.path.dirname(path))
        if path != original_path and original_path is not None:
            table.addRow(__("Original Filename"), os.path.basename(original_path))
            table.addRow(__("Original Folder"), os.path.dirname(original_path))

        table.addRow(__("Image Width"), pilImage.width)
        table.addRow(__("Image Height"), pilImage.height)
        table.addRow(__("File Size"), self._humanizeBytes(fileSize))
        table.addRow(__("Image Format"), pilImage.format_description)
        table.addRow(__("Color Channels"), pilImage.mode)
        table.addRow(__("Animated"), self._bool(getattr(pilImage, "is_animated", False)))
        frames = getattr(pilImage, "n_frames", 1)
        if frames > 1:
            table.addRow(__("Number of Frames"), frames)

    def _getExif(self, image: PILImage) -> dict[str, str]:
        """
        Gets the EXIF data from the image.
        """
        exif = {}
        info = image.getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif[decoded] = value

        return exif

    def _bool(self, value: bool) -> str:
        """
        Converts a boolean value to a string.
        """
        return __("Yes") if value else __("No")

    def _humanizeBytes(self, bytes: int) -> str:
        """
        Converts a number of bytes to a human-readable string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(bytes) < 1024.0:
                return "%3.1f %s" % (bytes, unit)
            bytes /= 1024.0
        return "%.1f %s" % (bytes, "YB")

    def _printHashes(self, table: PropertiesTable, image: Image):
        table.addHeader(__("Hashes"))
        hashes = image.hashes
        if len(hashes) == 0:
            table.addInfo(__("No hashes available"))
        else:
            for hash_type, hash in hashes.items():
                table.addRow(hash_type.upper(), hash)

    def _printExif(self, table: PropertiesTable, pilImage: PILImage):
        table.addHeader(__("EXIF Data"))
        exif = self._getExif(pilImage)
        if (len(exif) == 0):
            table.addInfo(__("No EXIF data available."))
        else:
            for key, value in exif.items():
                table.addRow(key, value)

    def _printFaceDetection(self, table: PropertiesTable, image: Image):
        table.addHeader(__("Face detection"))
        count = len(image.faces)
        if not image._processed:
            table.addInfo(__("Waiting for processing..."))
        elif (count == 0):
            table.addInfo(__("No faces detected."))
        elif (count == 1):
            table.addInfo(__("1 face detected."))
            self._printFaces(image.faces)
        else:
            table.addInfo(__("{count} faces detected.", count=count))
            self._printFaces(image.faces)

    def _printFaces(self, table: PropertiesTable, faces: list[Face]):
        for face in faces:
            pixmap = face.get_avatar_pixmap(64)
            group = face.group
            name = group.name if group is not None else __("Unknown")
            name = name if name != "" else __("Unknown")
            table.addPixmapRow(name, pixmap, value=face)


class MultiImageInfoProvider(InfoProvider):
    """
    Provides BASIC information about a group of selected images
    """
    def __init__(self, images: list[Image]):
        self._images = images

    def populate(self, table: PropertiesTable):
        """
        Populate the properties table with information about the selected object.
        """
        images = self._images
        count = len(images)
        label = __("Selected {count} images", count=count)
        table.addHeader(label)
        # print first 10 images
        for i in range(min(10, count)):
            table.addInfo(images[i].display_name)
        if count > 10:
            table.addInfo(__("And {count} more...", count=count - 10))


class ProjectInfoProvider(InfoProvider):
    """
    Provides information about a project.
    """

    def __init__(self, project: Project = None):
        self._project = project or Application.workspace().project()

    def populate(self, table: PropertiesTable):
        """
        Populate the properties table with information about the selected object.
        """
        project = self._project
        table.addHeader(__("Project Information"))
        table.addRow(__("Project Name"), project.name)
        table.addRow(__("Project Path"), project.path)
        table.addRow(__("Number of Images"), len(project.images))

        if project.is_portable:
            table.addRow(__("Portable Project"), __("Yes"))
            table.addInfo(__("Portable projects can be moved to another location or copied to another computer."))
        else:
            table.addRow(__("Portable Project"), __("No"))
            table.addInfo(__("Non-portable projects can only be opened on the computer they were created on."))
