
from ..Widgets.InspectorPanelBase import InspectorPanelBase

from ..Models import Image


class MainInspectorPanel(InspectorPanelBase):
    """
    A widget that displays a the properties of an image or a group of images.
    It shows the image itself, the basic information about the image, the EXIF data and the face detection results.
    """

    def setSelectedImages(self, images: list[Image]):
        """
        Sets the selected images.
        """
        self._selectedImages = images
        self._refresh()

    def selectedImages(self) -> list[Image]:
        """
        Gets the selected images.
        """
        return self._selectedImages

    def _refresh(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        count = len(self._selectedImages)
        if count == 0:
            self.inspectProject()
        elif count == 1:
            self.inspectImage(self._selectedImages[0])
        else:
            self.inspectImages(self._selectedImages)
