from ..Widgets.InspectorPanelBase import InspectorPanelBase
from ..Models import Face
from ..l10n import __


class FaceInspectorPanel(InspectorPanelBase):
    """
    A widget that displays information about a face.
    """

    _selectedFaces: list[Face] = []

    def setSelectedFaces(self, faces: list[Face]):
        """
        Sets the selected faces.
        """
        self._selectedFaces = faces
        self._refresh()

    def selectedFaces(self) -> list[Face]:
        """
        Gets the selected faces.
        """
        return self._selectedFaces

    def _refresh(self):
        """
        Refreshes the information displayed in the inspector panel.
        """
        count = len(self._selectedFaces)
        if count == 0:
            self.inspectNothing()
        elif count == 1:
            self.inspectFace(self._selectedFaces[0])
        else:
            self.inspectFaces(self._selectedFaces)

    def inspectNothing(self):
        """
        Inspects nothing.
        """
        self._table.clear()
        self._preview.setImage(None)
        self._table.addHeader(__("No face selected"))
        self._table.addInfo(__("Select a face to see its properties."))
