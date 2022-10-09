from PySide6 import QtCore, QtGui, QtWidgets
from .ClusteringService import find_merge_oportunities, MergeOportunity
from ..Widgets.PixmapDisplay import PixmapDisplay
from ..Models import Group, Project
from src.l10n import __


class _IconButton(QtWidgets.QPushButton):
    def __init__(self, text: str, iconPath: str, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the IconButton class.

        Args:
            text (str): The text to show.
            iconPath (str): The path to the icon.
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        self._icon = QtWidgets.QLabel()
        size = QtCore.QSize(32, 32)
        self._icon.setPixmap(QtGui.QPixmap(iconPath).scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self._icon.setAlignment(QtCore.Qt.AlignCenter)
        self._icon.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(self._icon)
        self._text = QtWidgets.QLabel(text)
        self._text.setAlignment(QtCore.Qt.AlignCenter)
        self._text.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(self._text)
        self.setLayout(layout)
        self.setFixedSize(120, 80)


class _AreSamePersonWidget(QtWidgets.QFrame):
    """
    A widget that shows to the user the best two candidate groups for merging and ask them
    whether the person is the same person or not. The two groups are shown as two faces.
    """
    yesClicked = QtCore.Signal()
    """Signal emitted when the user clicks the yes button."""

    noClicked = QtCore.Signal()
    """Signal emitted when the user clicks the no button."""

    skipClicked = QtCore.Signal()
    """Signal emitted when the user clicks the skip button."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the AreSamePersonWidget class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        self._group1: Group = None
        self._group2: Group = None

        self.setObjectName("AreSamePersonWidget")
        self.setStyleSheet("QFrame#AreSamePersonWidget { border: 2px solid #0078d7; border-radius: 5px; }")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        self.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)

        headerLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(headerLayout)

        title = QtWidgets.QLabel(__("Improve the results"))
        title.setAlignment(QtCore.Qt.AlignLeft)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0b3e66;")
        headerLayout.addWidget(title)

        self._progressLabel = QtWidgets.QLabel("", self)
        self._progressLabel.setAlignment(QtCore.Qt.AlignRight)
        self._progressLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._progressLabel.setStyleSheet("font-size: 12px; color: gray;")
        headerLayout.addWidget(self._progressLabel)

        description = QtWidgets.QLabel(__("Are they the same person or different people?"))
        description.setAlignment(QtCore.Qt.AlignCenter)
        description.setStyleSheet("font-size: 16px; color: black;")
        layout.addSpacing(5)
        layout.addWidget(description)

        imagesLayout = QtWidgets.QHBoxLayout()
        imagesLayout.setSpacing(40)
        layout.addSpacing(10)
        layout.addLayout(imagesLayout)
        layout.addSpacing(10)

        self._group1Image = PixmapDisplay(self)
        self._group1Image.setFixedSize(100, 100)
        self._group2Image = PixmapDisplay(self)
        self._group2Image.setFixedSize(100, 100)

        imagesLayout.addStretch(1)
        imagesLayout.addWidget(self._group1Image)
        imagesLayout.addWidget(self._group2Image)
        imagesLayout.addStretch(1)

        questionLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(questionLayout)

        self._yesButton = _IconButton(__("Same person"), "res/yes.png", self)
        self._yesButton.clicked.connect(self.yesClicked)
        self._noButton = _IconButton(__("Different people"), "res/no.png", self)
        self._noButton.clicked.connect(self.noClicked)
        self._skipButton = _IconButton(__("I'm not sure"), "res/unknown.png", self)
        self._skipButton.clicked.connect(self.skipClicked)

        questionLayout.addStretch(1)
        questionLayout.addWidget(self._yesButton)
        questionLayout.addWidget(self._noButton)
        questionLayout.addWidget(self._skipButton)
        questionLayout.addStretch(1)

    def setGroups(self, group1: Group, group2: Group) -> None:
        """
        Sets the groups to show to the user.

        Args:
            group1 (Group): The first group.
            group2 (Group): The second group.
        """
        self._group1 = group1
        self._group2 = group2

        w, h = self._group1Image.size().width(), self._group1Image.size().height()
        self._group1Image.setPixmap(group1.main_face.get_avatar_pixmap(w, h))

        w, h = self._group2Image.size().width(), self._group2Image.size().height()
        self._group2Image.setPixmap(group2.main_face.get_avatar_pixmap(w, h))

    def setProgress(self, current: int, total: int) -> None:
        """
        Sets the progress of the merge oportunities.

        Args:
            current (int): The current progress.
            total (int): The total progress.
        """
        self._progressLabel.setText(__("Question {current} of {total}", current=current, total=total))


class _DoneWidget(QtWidgets.QFrame):
    """
    A simple widget that shows a tilde icon and a "Thank you. All done for now" text and a "Close" button.
    Optionally, it can show a "Keep answering" button.
    """

    onDone = QtCore.Signal()
    """Signal emitted when the user clicks on the done button."""

    onKeepAnswering = QtCore.Signal()
    """Signal emitted when the user clicks on the keep answering button."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the DoneWidget class.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        self.setObjectName("DoneWidget")
        self.setStyleSheet("QFrame#DoneWidget { border: 2px solid #37c451; border-radius: 5px; }")
        self.setContentsMargins(5, 5, 5, 5)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)

        title = QtWidgets.QLabel(__("Improve the results"))
        title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        title.setAlignment(QtCore.Qt.AlignLeft)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #37c451;")
        layout.addWidget(title)

        horLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(horLayout)

        icon = QtWidgets.QLabel()
        icon.setPixmap(QtGui.QPixmap("res/smiling_sun.png"))
        icon.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        description = QtWidgets.QLabel(__("Thank you. All done for now."))
        description.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        description.setStyleSheet("font-size: 14px; color: black;")

        horLayout.addStretch(1)
        horLayout.addWidget(icon)
        horLayout.addSpacing(10)
        horLayout.addWidget(description)
        horLayout.addStretch(1)

        buttonsLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(buttonsLayout)

        self._doneButton = QtWidgets.QPushButton(__("Close"))
        self._doneButton.clicked.connect(self.onDone)

        self._keepAnsweringButton = QtWidgets.QPushButton(__("Keep answering"))
        self._keepAnsweringButton.clicked.connect(self.onKeepAnswering)

        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(self._keepAnsweringButton)
        buttonsLayout.addWidget(self._doneButton)
        buttonsLayout.addStretch(1)

    def setKeepAnsweringVisible(self, visible: bool) -> None:
        """
        Sets whether the keep answering button should be visible.

        Args:
            visible (bool): Whether the keep answering button should be visible.
        """
        self._keepAnsweringButton.setVisible(visible)

    def keepAnsweringVisible(self) -> bool:
        """
        Returns whether the keep answering button is visible.

        Returns:
            bool: Whether the keep answering button is visible.
        """
        return self._keepAnsweringButton.isVisible()


class MergingWizard(QtWidgets.QWidget):
    """
    A wizard that shows to the user two groups that are close to each other and ask them whether
    the two groups are the same person or not.
    """

    groupsMerged = QtCore.Signal(MergeOportunity)
    """Emitted when the user merges two groups."""

    groupsDontMerged = QtCore.Signal(MergeOportunity)
    """Emitted when the user doesn't merge two groups."""

    def __init__(self, project: Project, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize a new instance of the MergingWizard class.

        Args:
            project (Project): The project.
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._stackedWidget = QtWidgets.QStackedWidget(self)
        layout.addWidget(self._stackedWidget)

        self._areSamePersonWidget = _AreSamePersonWidget(self)
        self._areSamePersonWidget.yesClicked.connect(self._onYesClicked)
        self._areSamePersonWidget.noClicked.connect(self._onNoClicked)
        self._areSamePersonWidget.skipClicked.connect(self._onSkipClicked)
        self._stackedWidget.addWidget(self._areSamePersonWidget)

        self._doneWidget = _DoneWidget(self)
        self._doneWidget.onDone.connect(self._onDone)
        self._doneWidget.onKeepAnswering.connect(self._onKeepAnswering)
        self._stackedWidget.addWidget(self._doneWidget)

        self._stackedWidget.setCurrentWidget(self._areSamePersonWidget)

        self._ignoredOportunities: list[MergeOportunity] = []

        self._project = project
        if len(self._project.groups) > 1:
            self.recalculateMergeOpportunities(autoStart=True)

    def recalculateMergeOpportunities(self, autoStart: bool = True) -> None:
        """
        Recalculates the merge opportunities.

        Args:
            autoStart (bool): Whether to automatically start the wizard if there are merge opportunities.
        """
        self._mergeOportunities = find_merge_oportunities(self._project.groups, self._ignoredOportunities)
        total = len(self._mergeOportunities)
        self._currentIndex = 0

        if autoStart and total > 0:
            self.nextQuestion()

    def nextQuestion(self) -> None:
        """
        Shows the next merge oportunity to the user.
        """
        total = len(self._mergeOportunities)
        if total == 0:
            self._stackedWidget.setCurrentWidget(self._doneWidget)
            self.hide()  # Don't show the wizard if there are no merge opportunities.
            return

        if self._currentIndex < total:
            oportunity = self._mergeOportunities[self._currentIndex]
            self._currentIndex += 1
            self._areSamePersonWidget.setGroups(oportunity.group1, oportunity.group2)
            self._areSamePersonWidget.setProgress(self._currentIndex, total)
            self._stackedWidget.setCurrentWidget(self._areSamePersonWidget)
        else:
            self.recalculateMergeOpportunities(autoStart=False)
            self._doneWidget.setKeepAnsweringVisible(total > 0)
            self._stackedWidget.setCurrentWidget(self._doneWidget)

    def _oportunity(self) -> MergeOportunity:
        """
        Returns the current merge oportunity.

        Returns:
            MergeOportunity: The current merge oportunity.
        """
        return self._mergeOportunities[self._currentIndex - 1]

    @QtCore.Slot()
    def _onYesClicked(self) -> None:
        op = self._oportunity()
        op.group1.merge(op.group2)
        self._project.remove_group(op.group2)
        self._removeGroupFromIgnored(op.group2)
        self._removeGroupFromOportunities(op.group2)
        self.groupsMerged.emit(op)
        self.nextQuestion()

    @QtCore.Slot()
    def _onNoClicked(self) -> None:
        op = self._oportunity()
        op.group1.dont_merge_with.add(op.group2)
        op.group2.dont_merge_with.add(op.group1)
        self.groupsDontMerged.emit(op)
        self.nextQuestion()

    @QtCore.Slot()
    def _onSkipClicked(self) -> None:
        op = self._oportunity()
        self._ignoredOportunities.append(op)
        self.nextQuestion()

    @QtCore.Slot()
    def _onDone(self) -> None:
        """
        Called when the user clicks on the done button.
        """
        self.hide()

    @QtCore.Slot()
    def _onKeepAnswering(self) -> None:
        """
        Called when the user clicks on the keep answering button.
        """
        self.nextQuestion()

    def _removeGroupFromIgnored(self, group: Group) -> None:
        """
        Removes a group from the ignored oportunities.

        Args:
            group (Group): The group to remove.
        """
        self._ignoredOportunities = [op for op in self._ignoredOportunities if op.group1 != group and op.group2 != group]

    def _removeGroupFromOportunities(self, group: Group) -> None:
        """
        Removes a group from the oportunities.

        Args:
            group (Group): The group to remove.
        """
        self._mergeOportunities = [op for op in self._mergeOportunities if op.group1 != group and op.group2 != group]
