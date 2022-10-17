import glob
import os

from PySide6 import QtWidgets

from ..Application import Application
from ..l10n import __
from ..Models import Image
from ..ProjectFile.ProjectFileReader import ProjectFileReader
from ..ProjectFile.ProjectFileWriter import ProjectFileWriter
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

        skippedImages = []

        def onProgress(index: int, count: int, image: Image):
            bussyModal.setSubtitle(__("@project_manager.adding_images.subtitle", current=str(index + 1), total=str(count)))

        def onImageError(e: Exception, image: Image):
            nonlocal skippedImages
            print(f"Error adding image: {image.path}. Error: {e}")
            skippedImages.append(image)

        def addFilesWorker():
            self._workspace.addImages(file_paths, onProgress=onProgress, onImageError=onImageError)

        bussyModal.exec(addFilesWorker)

        if len(skippedImages) > 0:
            listStr = self._getImagesList(skippedImages)
            QtWidgets.QMessageBox.warning(
                parent, __("@project_manager.add_images_error.title"),
                __("@project_manager.add_images_error.message", list=listStr))

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

            paths = [folder_path + "/" + image.display_name for image in images]
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
            parent,
            title=__("@project_manager.loading_project.title"),
            subtitle=__("@project_manager.loading_project.subtitle"))

        # Skipped images are images that could not be loaded
        imagesSkipped: list[Image] = []

        def openProjectWorker():
            reader = ProjectFileReader(on_progress=onProgress, on_image_error=onImageError)
            project = reader.read(file_path)
            self._workspace.setProject(project)

        def onProgress(index: int, count: int, image: Image):
            bussyModal.setSubtitle(__("@project_manager.loading_project.subtitle", current=index + 1, total=count))

        def onImageError(error: Exception, image: Image) -> bool:
            nonlocal imagesSkipped
            print(f"Error loading image {image.display_name}: {error}")
            imagesSkipped.append(image)
            return True

        bussyModal.exec(openProjectWorker)

        if len(imagesSkipped) > 0:
            if self._askToRemoveSkippedImages(parent, imagesSkipped):
                for image in imagesSkipped:
                    self._workspace.project().remove_image(image)

    def _askToRemoveSkippedImages(self, parent: QtWidgets.QWidget, imagesSkipped: list[Image]) -> bool:
        """
        Asks the user if the skipped images should be removed from the project.

        Args:
            parent (QWidget): The parent widget.
            imagesSkipped (list[Image]): The list of images that were skipped from loading.

        Returns:
            bool: True if the images should be removed, False otherwise.
        """
        listStr = self._getImagesList(imagesSkipped)
        message = __("@project_manager.skipped_images.message", list=listStr)
        return QtWidgets.QMessageBox.question(
            parent, __("@project_manager.skipped_images.title"), message) == QtWidgets.QMessageBox.Yes

    def _getImagesList(self, images: list[Image], topCount=5) -> str:
        """
        Gets a string representation of the list of images. For example:
        - Image1.png
        - Image2.png
        - Image3.png
        - And 32 more...

        Args:
            images (list[Image]): The list of images.
            topCount (int, optional): The number of images to show at the top. Defaults to 5.

        Returns:
            str: The string representation.
        """
        topList = [image.display_name for image in images[:topCount]]
        if len(images) > topCount:
            topList.append(__("@project_manager.and_more", count=len(images) - topCount))
        listFormat = "🡲 {item}"  # Unicode right arrow. I think Win8 doesn't support this in it's default font.
        return "\n".join([listFormat.format(item=item) for item in topList])

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

    def _saveProjectCore(self, parent: QtWidgets.QWidget, file_path: str, portable: bool = None) -> None:
        """
        Saves the project to the specified file path and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.
            file_path (str): The file path.
            portable (bool): Whether to save the project in portable mode. By default, the current mode is used.
        """
        bussyModal = BussyModal(
            parent, title=__("@project_manager.saving_project.title"), subtitle=__("@project_manager.saving_project.subtitle"))

        def onImageCopied(current: int, total: int, image: Image):
            bussyModal.setSubtitle(__("@project_manager.saving_project.copying", current=current + 1, total=total))

        def saveProjectWorker():
            nonlocal portable
            project = self._workspace.project()
            writer = ProjectFileWriter(project, portable=portable, on_image_copied=onImageCopied)
            writer.write(file_path)
            self._workspace.setDirty(False)

        bussyModal.exec(saveProjectWorker)

    def saveProjectAs(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select a project file and saves the project to it.

        Args:
            parent (QWidget): The parent widget.
        """
        current_path = self._workspace.project().path
        file_dir = os.path.dirname(current_path) if current_path else ""

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, __("@project_manager.select_project_save_caption"), file_dir,
            self._projectFilter)

        if file_path:
            portable = self._askForPortableMode(parent)
            self._saveProjectCore(parent, file_path, portable=portable)

    def _askForPortableMode(self, parent: QtWidgets.QWidget) -> bool:
        """
        Asks the user if they want to save the project in portable mode.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            bool: True if the user wants to save in portable mode, False otherwise.
        """
        yesNoFlags = QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No

        result = QtWidgets.QMessageBox.question(
            parent, __("@project_manager.portable_mode.title"),
            __("@project_manager.portable_mode.message"),
            yesNoFlags,
            QtWidgets.QMessageBox.StandardButton.No)

        return result == QtWidgets.QMessageBox.StandardButton.Yes

    def saveProject(self, parent: QtWidgets.QWidget) -> None:
        """
        Saves the project to the current file.

        Args:
            parent (QWidget): The parent widget.
        """
        path = self._workspace.project().path
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
