import glob
import logging
import os
from typing import Callable

from PySide6 import QtWidgets

from startfile import startfile
from .l10n import __
from .Models import Image
from .Widgets.BussyModal import BussyModal
from .Workspace import Workspace
from . import constants


class ProjectManager:
    """
    The project manager class provides high-level methods to manage the project
    and show dialogs to the user. This class has knowledge of Qt and the UI.
    On the other hand, the workspace class is a lower level class that has no
    knowledge of Qt and the UI. This class provides the same functionality as
    the Workspace but for the UI to interact with the user.
    """

    _importExtensions = constants.app_import_extensions

    _importFilter = __("Images") + " (" + " ".join(["*." + ext for ext in _importExtensions]) + ")"

    _exportExtensions = constants.app_export_extensions

    _exportFilter = __("Images") + " (" + " ".join(["*." + ext for ext in _exportExtensions]) + ")"

    _projectExtension = constants.app_project_extension

    _projectFilter = __("Phantom Project") + " (*." + _projectExtension + ")"

    _warningImageCount = 2000

    def __init__(self, workspace: Workspace) -> None:
        """
        Initializes a new instance of the ProjectManager class.

        Args:
            workspace (Workspace): The workspace
        """
        self._workspace = workspace

    def addFolder(self, parent: QtWidgets.QWidget, folder_path: str = None) -> None:
        """
        Asks the user to select a folder and adds it to the project.

        Args:
            parent (QWidget): The parent widget.
            folder_path (str): The folder path. If None, the user will be asked to select a folder.

        Returns:
            list[str]: The list of file paths.
        """

        if folder_path is None:
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                parent, __("@project_manager.select_folder_caption"), ""
            )
            if not folder_path:
                return

        glob_base = folder_path + "/**/*."
        filePaths = []
        for ext in self._importExtensions:
            filePaths += glob.glob(glob_base + ext, recursive=True)

        # Show a dialog asking the user to confirm the files to add.
        count = len(filePaths)
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

        images = [Image(path) for path in filePaths]
        self.addImagesToProject(parent, images)

    def addImagesToProject(self, parent: QtWidgets.QWidget, images: list[Image]) -> None:
        """
        Adds the images to the project and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.
            images (list[Image]): The images to add.
        """
        bussyModal = BussyModal(parent, title=__("@project_manager.adding_images.title"))

        skippedImages = []

        def onProgress(index: int, count: int, image: Image):
            bussyModal.setSubtitle(__("@project_manager.adding_images.subtitle", current=str(index + 1), total=str(count)))

        def onImageError(e: Exception, image: Image):
            nonlocal skippedImages
            logging.warn(f"Error adding image: {image.path}. Error: {e}")
            skippedImages.append(image)

        def addFilesWorker():
            self._workspace.addImages(images, onProgress=onProgress, onImageError=onImageError)

        bussyModal.exec(addFilesWorker)

        if len(skippedImages) > 0:
            listStr = self._getImagesList(skippedImages)
            QtWidgets.QMessageBox.warning(
                parent, __("@project_manager.add_images_error.title"),
                __("@project_manager.add_images_error.message", list=listStr))

    def addImageToProject(self, parent: QtWidgets.QWidget, image: Image) -> None:
        """
        Adds the image to the project and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.
            image (Image): The image to add.
        """
        self.addImagesToProject(parent, [image])

    def importImages(self, parent: QtWidgets.QWidget) -> None:
        """
        Asks the user to select images and adds them to the project.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            list[str]: The list of file paths.
        """

        filePaths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent, __("@project_manager.select_images_caption"), "",
            self._importFilter)

        if not filePaths:
            return

        images = [Image(path) for path in filePaths]
        self.addImagesToProject(parent, images)

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
            filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent, __("@project_manager.select_export_file_caption"), "",
                self._exportFilter)
            if not filePath:
                return
            self._exportImagesCore(parent, [images[0]], [filePath])
        else:
            # If there are multiple images, export a folder.
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                parent, __("@project_manager.select_export_folder_caption"), "")

            paths = [folder_path + "/" + image.display_name for image in images]
            self._exportImagesCore(parent, images, paths)

    def exportImage(self, parent: QtWidgets.QWidget, image: Image, addToProject: bool = False) -> None:
        """
        Asks the user to select a file and exports the image to it.

        Args:
            parent (QWidget): The parent widget.
            image (Image): The image to export.
            addToProject (bool): If True, the exported image will be added to the project.
        """
        self.exportImages(parent, [image])
        if addToProject:
            self.addImageToProject(parent, image)

    def exportImageLazy(
            self, parent: QtWidgets.QWidget, generateImageFn: Callable[[], Image], addToProject: bool = False) -> Image:
        """
        Asks the user to select a file, then after the user has
        properly selected a file, the image is generated and exported.

        Args:
            parent (QWidget): The parent widget.
            generateImageFn (Callable[[], Image]): A function that generates the image to export.
            addToProject (bool): If True, the exported image will be added to the project.

        Returns:
            Image: The generated image or None if the user cancelled the export.
        """
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, __("@project_manager.select_export_file_caption"), "",
            self._exportFilter)
        if not filePath:
            return None

        image = generateImageFn()
        self._exportImagesCore(parent, [image], [filePath])
        if addToProject:
            self.addImageToProject(parent, image)

        return image

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
                path = paths[i]
                image.save(path)
                if image.path is None:
                    image.path = path
                bussyModal.setSubtitle(__("@project_manager.exporting_images.subtitle", current=i + 1, total=count))

        bussyModal.exec(exportImagesWorker)

    def openProject(self, parent: QtWidgets.QWidget, file_path: str = None) -> None:
        """
        Asks the user to select a project file and opens it.

        Args:
            parent (QWidget): The parent widget.
            file_path (str): The path to the project file to open. If None, the user will be asked to select a file.
        """
        if file_path is None:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent, __("@project_manager.select_project_open_caption"), "",
                self._projectFilter)

            if not filePath:
                return

        # Load the project with a bussy modal.
        bussyModal = BussyModal(
            parent,
            title=__("@project_manager.loading_project.title"),
            subtitle=__("@project_manager.loading_project.subtitle"))

        # Skipped images are images that could not be loaded
        imagesSkipped: list[Image] = []

        def openProjectWorker():
            from .ProjectFile.ProjectFileReader import ProjectFileReader  # Avoids circular import
            reader = ProjectFileReader(on_progress=onProgress, on_image_error=onImageError)
            project = reader.read(filePath)
            self._workspace.setProject(project)

        def onProgress(index: int, count: int, image: Image):
            bussyModal.setSubtitle(__("@project_manager.loading_project.progress", current=index + 1, total=count))

        def onImageError(error: Exception, image: Image) -> bool:
            nonlocal imagesSkipped
            logging.warn(f"Error loading image {image.display_name}: {error}")
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
            from .ProjectFile.ProjectFileWriter import ProjectFileWriter  # Avoids circular import
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
        currentPath = self._workspace.project().path
        file_dir = os.path.dirname(currentPath) if currentPath else ""

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

    def closeProject(self, parent: QtWidgets.QWidget) -> bool:
        """
        Closes the project. If there are unsaved changes, asks the user to save them.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            bool: True if the project was closed, False otherwise.
        """
        if self._checkUnsavedChanges(parent):
            self._workspace.closeProject()
            return True
        return False

    def ensureModelsAreDownloaded(self, parent: QtWidgets.QWidget = None) -> bool:
        """
        Downloads the latest models if required and shows a bussy modal.

        Args:
            parent (QWidget): The parent widget.

        Returns:
            True if the models were updated or no update was required,
            False if the update failed or the user cancelled the update.
        """
        from .Application import Application  # Avoids circular import

        downloader = Application.instance().modelsDownloader()

        if downloader.models_are_updated():
            return True

        bussyModal = BussyModal(
            parent, title=__("@project_manager.downloading_models.title"),
            subtitle=__("@project_manager.downloading_models.subtitle"))

        def extractProgress(current: int, total: int):
            bussyModal.setSubtitle(__("@project_manager.downloading_models.extracting", current=current, total=total))

        def humanizeMb(size: int) -> str:
            return "{:.2f} MB".format(size / 1024 / 1024) if size else "??? MB"

        def downloadProgress(current: int, total: int):
            currentMb = humanizeMb(current)
            totalMb = humanizeMb(total)
            percent = int(current / total * 100)
            bussyModal.setSubtitle(
                __("@project_manager.downloading_models.downloading", current=currentMb, total=totalMb, percent=percent))

        error: Exception = None

        def updateModelsWorker():
            nonlocal downloader, error
            downloader.on_download_progress = downloadProgress
            downloader.on_extract_progress = extractProgress
            try:
                downloader.download_models()
                error = None
            except Exception as e:
                logging.error("Error updating models: {}".format(e))
                error = e

        bussyModal.exec(updateModelsWorker)

        if error:
            QtWidgets.QMessageBox.critical(
                parent, __("@project_manager.downloading_models.error.title"),
                __("@project_manager.downloading_models.error.message", error=error))
            from .Application import Application
            Application.instance().quit()
            return False

        return True

    def _checkImageFileExists(self, image: Image) -> bool:
        if image.is_virtual:
            return False
        if not os.path.exists(image.path):
            QtWidgets.QMessageBox.critical(
                self, __("Image file not found"),
                __("Image file {path} not found.", path=image.path))
            return False
        return True

    def openImageExternally(self, image: Image) -> None:
        if not self._checkImageFileExists(image):
            return
        startfile(image.path)

    def openImageInExplorer(self, image: Image) -> None:
        if not self._checkImageFileExists(image):
            return
        startfile(os.path.dirname(image.path))
