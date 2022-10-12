import os
from PySide6 import QtWidgets
import glob
from ..Models import Image
from src.l10n import __
from ..Application import Application


class ProjectManager:
    """
    The project manager class provides high-level methods to manage the project
    and show dialogs to the user. This class has knowledge of Qt and the UI.
    On the other hand, the workspace class is a lower level class that has no
    knowledge of Qt and the UI.
    """

    _importExtensions = ["png", "jpg", "jpeg", "tiff", "tif", "bmp"]

    _importFilter = __("Images") + " (*.png *.jpg *.jpeg *.tiff *.tif *.bmp)"

    _exportExtensions = ["png", "jpg"]

    _exportFilter = __("Images") + " (*.png *.jpg)"

    _projectFilter = __("Phantom Project") + " (*.phantom)"

    def __init__(self) -> None:
        """
        Initializes a new instance of the ProjectManager class.
        """
        self._workspace = Application.workspace()

    def addFolder(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select a folder and adds it to the project.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            list[str]: The list of file paths.
        """

        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            parent, __("Select a folder to add to the project"), "", QtWidgets.QFileDialog.ShowDirsOnly)

        if folder_path:
            glob_base = folder_path + "/**/*."
            file_paths = []
            for ext in self._importExtensions:
                file_paths += glob.glob(glob_base + ext, recursive=True)

            # Show a dialog asking the user to confirm the files to add.
            count = len(file_paths)
            if count == 0:
                QtWidgets.QMessageBox.warning(
                    parent, __("No images found"),
                    __("No images found in the selected folder. Please select a folder with images."))
                return
            else:
                result = QtWidgets.QMessageBox.question(
                    parent, __("Add images to the project"),
                    __("Found {count} images in the selected folder. Do you want to add them to the project?", count=count),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

                if result == QtWidgets.QMessageBox.No:
                    return

            # Add the files to the project.
            for file_path in file_paths:
                self._workspace.addImage(file_path)

    def addImages(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select images and adds them to the project.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            list[str]: The list of file paths.
        """

        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent, __("Select images to add to the project"), "", self._importFilter)

        if file_paths:
            # Add the files to the project.
            for file_path in file_paths:
                self._workspace.addImage(file_path)

    def exportImages(self, parent: QtWidgets.QWidget, images: list[Image]) -> None:
        """
        Asks the user to select a folder and exports the images to it.

        Args:
            images (list[Image]): The images to export.
            parent (QWidget): The parent widget.
        """

        if len(images) == 0:
            # Export all images.
            images = self._workspace.project().images

        if len(images) == 0:
            QtWidgets.QMessageBox.warning(
                parent, __("No images to export"),
                __("No images to export. Please add images to the project."))
            return

        if len(images) == 1:
            # If there is only one image, export a single file.
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent, __("Export image"), "", self._exportFilter)

            if file_path:
                images[0].save(file_path)
        else:
            # If there are multiple images, export a folder.
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                parent, __("Select a folder to export the images to"), "", QtWidgets.QFileDialog.ShowDirsOnly)

            if folder_path:
                for image in images:
                    image.save(folder_path + "/" + image.basename)

    def openProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select a project file and opens it.

        Args:
            parent (QWidget): The parent widget.
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent, __("Select a project file"), "", self._projectFilter)

        if file_path:
            self._workspace.openProject(file_path)

    def newProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Creates a new project. If there are unsaved changes, asks the user to save them.

        Args:
            parent (QWidget): The parent widget.
        """
        if self._workspace.isDirty():
            result = QtWidgets.QMessageBox.question(
                parent, __("New project"), __("The current project has unsaved changes. Do you want to continue?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

            if result == QtWidgets.QMessageBox.No:
                return

        self._workspace.newProject()

    def saveProjectAs(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select a project file and saves the project to it.

        Args:
            parent (QWidget): The parent widget.
        """
        current_path = self._workspace.project().file_path
        file_dir = os.path.dirname(current_path) if current_path else ""

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, __("Save project"), file_dir, self._projectFilter)

        if file_path:
            self._workspace.saveProject(file_path)

    def saveProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Saves the project to the current file.

        Args:
            parent (QWidget): The parent widget.
        """
        if self._workspace.project().file_path:
            self._workspace.saveProject()
        else:
            self.saveProjectAs(parent)
