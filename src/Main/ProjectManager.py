import glob
import os

from PySide6 import QtWidgets

from ..Application import Application
from ..l10n import __
from ..Models import Image
from ..Widgets.BussyModal import BussyModal


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

    _warningImageCount = 2000

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
            parent, __("@project_manager.select_folder_caption"), ""
        )

        if not folder_path:
            return

        glob_base = folder_path + "/**/*."
        file_paths = []
        for ext in self._importExtensions:
            file_paths += glob.glob(glob_base + ext, recursive=True)

        # Show a dialog asking the user to confirm the files to add.
        count = len(file_paths)
        if count == 0:
            formats = ", ".join(self._importExtensions)
            QtWidgets.QMessageBox.warning(
                parent, __("@project_manager.no_images_found.title"),
                __("@project_manager.no_images_found.message", formats=formats))
            return
        elif count > self._warningImageCount:
            result = QtWidgets.QMessageBox.warning(
                parent, __("@project_manager.many_images_found.title"),
                __("@project_manager.many_images_found.message", count=count),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return
        else:
            result = QtWidgets.QMessageBox.question(
                parent, __("@project_manager.add_images.title"),
                __("@project_manager.add_images.message", count=count),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return

        # Add the files to the project.
        # show a bussy modal
        self._addImagesCore(parent, file_paths)

    def _addImagesCore(self, parent: QtWidgets.QWidget, file_paths: list[str]) -> None:
        """
        Adds the images to the project and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.
            file_paths (list[str]): The list of file paths.
        """
        bussyModal = BussyModal(parent, title=__("@project_manager.adding_images.title"))

        def onImageLoadedCallback(image: Image, index: int, count: int):
            bussyModal.setSubtitle(__("@project_manager.adding_images.subtitle", current=str(index + 1), total=str(count)))

        def addFilesWorker():
            self._workspace.addImages(file_paths, onImageLoadedCallback)

        bussyModal.exec(addFilesWorker)

    def addImages(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select images and adds them to the project.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            list[str]: The list of file paths.
        """

        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent, __("@project_manager.select_images_caption"), "",
            self._importFilter)

        if not file_paths:
            return

        self._addImagesCore(parent, file_paths)

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
                parent, __("@project_manager.no_images_to_export.title"),
                __("@project_manager.no_images_to_export.message"))
            return

        if len(images) == 1:
            # If there is only one image, export a single file.
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent, __("@project_manager.select_export_file_caption"), "",
                self._exportFilter)
            if not file_path:
                return
            self._exportImagesCore(parent, [images[0]], [file_path])
        else:
            # If there are multiple images, export a folder.
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                parent, __("@project_manager.select_export_folder_caption"), "")

            paths = [folder_path + "/" + image.basename for image in images]
            self._exportImagesCore(parent, images, paths)

    def _exportImagesCore(self, parent: QtWidgets.QWidget, images: list[Image], paths: list[str]) -> None:
        """
        Exports the images to the specified paths and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.
            images (list[Image]): The images to export.
            paths (list[str]): The paths to export to. Must be the same length as images.
        """
        bussyModal = BussyModal(parent, title=__("@project_manager.exporting_images.title"))

        def exportImagesWorker():
            count = len(images)
            for i, image in enumerate(images):
                image.save(paths[i])
                bussyModal.setSubtitle(__("@project_manager.exporting_images.subtitle", current=i + 1, total=count))

        bussyModal.exec(exportImagesWorker)

    def openProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select a project file and opens it.

        Args:
            parent (QWidget): The parent widget.
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent, __("@project_manager.select_project_open_caption"), "",
            self._projectFilter)

        if not file_path:
            return

        # Load the project with a bussy modal.
        bussyModal = BussyModal(
            parent, title=__("@project_manager.loading_project.title"), subtitle=__("@project_manager.loading_project.subtitle"))

        def openProjectWorker():
            self._workspace.openProject(file_path)

        bussyModal.exec(openProjectWorker)

    def _checkUnsavedChanges(self, parent: QtWidgets.QWidget) -> bool:
        """
        Checks if there are unsaved changes and asks the user if they want to save them.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            bool: True if the user wants to continue, False if the user wants to cancel.
        """
        if self._workspace.isDirty():
            yesNoCancelFlags = QtWidgets.QMessageBox.StandardButton.Yes \
                    | QtWidgets.QMessageBox.StandardButton.No \
                    | QtWidgets.QMessageBox.StandardButton.Cancel

            result = QtWidgets.QMessageBox.question(
                parent, __("@project_manager.unsaved_changes.title"),
                __("@project_manager.unsaved_changes.message"),
                yesNoCancelFlags,
                QtWidgets.QMessageBox.StandardButton.Yes)

            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self.saveProject(parent)
            elif result == QtWidgets.QMessageBox.StandardButton.Cancel:
                return False

        return True

    def newProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Creates a new project. If there are unsaved changes, asks the user to save them.

        Args:
            parent (QWidget): The parent widget.
        """
        if not self._checkUnsavedChanges(parent):
            return
        self._workspace.newProject()

    def _saveProjectCore(self, parent: QtWidgets.QWidget, file_path: str) -> None:
        """
        Saves the project to the specified file path and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.
            file_path (str): The file path.
        """
        bussyModal = BussyModal(
            parent, title=__("@project_manager.saving_project.title"), subtitle=__("@project_manager.saving_project.subtitle"))

        def saveProjectWorker():
            self._workspace.saveProject(file_path)

        bussyModal.exec(saveProjectWorker)

    def saveProjectAs(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select a project file and saves the project to it.

        Args:
            parent (QWidget): The parent widget.
        """
        current_path = self._workspace.project().file_path
        file_dir = os.path.dirname(current_path) if current_path else ""

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, __("@project_manager.select_project_save_caption"), file_dir,
            self._projectFilter)

        if file_path:
            self._saveProjectCore(parent, file_path)

    def saveProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Saves the project to the current file.

        Args:
            parent (QWidget): The parent widget.
        """
        path = self._workspace.project().file_path
        if path:
            self._saveProjectCore(parent, path)
        else:
            self.saveProjectAs(parent)

    def closeProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Closes the project. If there are unsaved changes, asks the user to save them.

        Args:
            parent (QWidget): The parent widget.
        """
        if not self._checkUnsavedChanges(parent):
            return
        self._workspace.closeProject()
