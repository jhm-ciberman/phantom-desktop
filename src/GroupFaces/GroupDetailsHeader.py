from PySide6 import QtCore, QtGui, QtWidgets
from ..Widgets.PixmapDisplay import PixmapDisplay
from ..Models import Group
from ..l10n import __


class GroupDetailsHeaderWidget(QtWidgets.QWidget):
    """
    The header for the group details
    """

    renameGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Rename group" action is triggered."""

    combineGroupTriggered = QtCore.Signal(Group)
    """Emited when the "Combine group" action is triggered."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the GroupDetailsHeaderWidget class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)
        self._group = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setFixedHeight(84)  # 64 + 10 + 10

        headerLayout = QtWidgets.QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(headerLayout)

        self._mainFaceIcon = PixmapDisplay()
        self._mainFaceIcon.setFixedSize(64, 64)
        headerLayout.addWidget(self._mainFaceIcon)

        infoLayout = QtWidgets.QVBoxLayout()
        infoLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        infoLayout.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        infoLayout.setContentsMargins(10, 0, 0, 0)
        headerLayout.addLayout(infoLayout)

        infoLayoutTop = QtWidgets.QHBoxLayout()
        infoLayout.addLayout(infoLayoutTop)

        self._nameLabel = QtWidgets.QLabel()
        self._nameLabel.setFont(QtGui.QFont("Arial", 20))
        self._nameLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self._nameLabel.setText("")
        infoLayoutTop.addWidget(self._nameLabel)

        self._editNameButton = QtWidgets.QPushButton(QtGui.QIcon("res/img/edit.png"), __("Edit name"))
        self._editNameButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._editNameButton.setContentsMargins(40, 0, 0, 0)
        self._editNameButton.clicked.connect(self._onEditNameClicked)
        infoLayoutTop.addWidget(self._editNameButton)

        self._combineGroupButton = QtWidgets.QPushButton(__("Combine group"))
        self._combineGroupButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._combineGroupButton.setContentsMargins(20, 0, 0, 0)
        self._combineGroupButton.clicked.connect(self._onCombineGroupClicked)
        infoLayoutTop.addWidget(self._combineGroupButton)

        self._subtitleLabel = QtWidgets.QLabel()
        self._subtitleLabel.setFont(QtGui.QFont("Arial", 12))
        self._editNameButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._subtitleLabel.setText("")
        self._subtitleLabel.setStyleSheet("color: gray;")
        infoLayout.addWidget(self._subtitleLabel)

    def setGroup(self, group: Group) -> None:
        """
        Set the group to display.

        Args:
            group (Group): The group to display.
        """
        self._group = group

        w, h = self._mainFaceIcon.size().width(), self._mainFaceIcon.size().height()
        self._mainFaceIcon.setPixmap(group.main_face.get_avatar_pixmap(w, h))
        name = group.name if group.name else __("Add a name to this person")
        self._nameLabel.setText(name)
        uniqueImagesCount = group.count_unique_images()
        if uniqueImagesCount > 1:
            self._subtitleLabel.setText(__("{count} images", count=uniqueImagesCount))
        else:
            self._subtitleLabel.setText(__("{count} image", count=uniqueImagesCount))
        titleColor = "black" if group.name else "#0078d7"
        self._nameLabel.setStyleSheet(f"color: {titleColor};")

    def refresh(self) -> None:
        """
        Refresh the widget.
        """
        self.setGroup(self._group)

    @QtCore.Slot()
    def _onEditNameClicked(self) -> None:
        """
        Called when the edit name button is clicked.
        """
        self.renameGroupTriggered.emit(self._group)

    @QtCore.Slot()
    def _onCombineGroupClicked(self) -> None:
        """
        Called when the combine group button is clicked.
        """
        self.combineGroupTriggered.emit(self._group)
