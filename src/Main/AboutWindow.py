from dataclasses import dataclass
from PySide6 import QtCore, QtGui, QtWidgets

from ..Application import Application
from ..l10n import __

from .. import constants


@dataclass(frozen=True, slots=True)
class Title:
    """A title in bold."""
    text: str


@dataclass(frozen=True, slots=True)
class Line:
    """A person with a username between parentheses. When the username is clicked, the link is opened."""
    name: str
    username: str
    link: str


credits = [
    Title(__("Phantom Desktop developed by:")),
    Line("Javier \"Ciberman\" Mora", "@jhm-ciberman", "https://github.com/jhm-ciberman"),

    Title(__("Phantom Core developed by:")),
    Line("Bruno Constanzo", "@bconstanzo", "https://github.com/bconstanzo"),

    Title(__("Special thanks to:")),
    Line("Santiago Trigo", "", ""),
    Line("Fernando Zagnoni", "", ""),
    Line("Matias N. Goldberg", "@darksylinc", "https://github.com/darksylinc"),
    Line("InfoLab", "info-lab.org.ar", "http://info-lab.org.ar/"),
    Line("Universidad Fasta", "ufasta.edu.ar", "https://www.ufasta.edu.ar/"),
    Line("Fluency Icons by Icons8", "icons8.com", "https://icons8.com/"),
]

logos = [
    "res/img/ufasta.png",
    "res/img/infolab.png",
]


class AboutWindow(QtWidgets.QDialog):
    """
    A dialog that displays information about the application.
    """

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initializes a new instance of the AboutWindow class.
        """
        super().__init__(parent)
        self.setWindowTitle(__("About Phantom Desktop"))
        self.setWindowFlags(QtCore.Qt.MSWindowsFixedSizeDialogHint | QtCore.Qt.WindowTitleHint)
        self.setWindowIcon(QtGui.QIcon("res/img/icon.png"))

        # Disable resizing
        self.setSizeGripEnabled(False)

        self._createUi()

    def _createUi(self) -> None:
        """
        Creates the user interface.
        """
        self._logoLabel = QtWidgets.QLabel()
        self._logoLabel.setPixmap(QtGui.QPixmap("res/img/icon.png"))
        self._logoLabel.setAlignment(QtCore.Qt.AlignCenter)

        self._titleLabel = QtWidgets.QLabel(__("Phantom Desktop"))
        self._titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._titleLabel.setFont(QtGui.QFont("Segoe UI", 20, QtGui.QFont.Weight.Bold))

        self._versionLabel = QtWidgets.QLabel(__("Version {version}", version=Application.instance().applicationVersion()))
        self._versionLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._versionLabel.setFont(QtGui.QFont("Segoe UI", 10))

        self._descriptionLabel = QtWidgets.QLabel(
            __("Phantom Desktop is a free and open source desktop application for forensic image processing."))
        self._descriptionLabel.setAlignment(QtCore.Qt.AlignCenter)
        self._descriptionLabel.setFont(QtGui.QFont("Segoe UI", 10))
        self._descriptionLabel.setWordWrap(True)

        github_link = constants.app_repo_url
        image_link = "res/img/github_16.png"
        links_str = f"<img src=\"{image_link}\" width=\"16\" height=\"16\"/>    <a href=\"{github_link}\">GitHub</a>"
        self._linksLabel = QtWidgets.QLabel(links_str)
        self._linksLabel.setOpenExternalLinks(True)
        self._linksLabel.setAlignment(QtCore.Qt.AlignCenter)

        self._creditsWidget = self._initializeCredits()

        # Button centered
        self._buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self._buttonBox.accepted.connect(self.accept)

        leftColumn = QtWidgets.QVBoxLayout()
        leftColumn.addWidget(self._logoLabel)
        leftColumn.addWidget(self._titleLabel)
        leftColumn.addWidget(self._versionLabel)
        leftColumn.addWidget(self._descriptionLabel)
        leftColumn.addWidget(self._linksLabel)

        layoutTop = QtWidgets.QHBoxLayout()
        layoutTop.addStretch()
        layoutTop.addLayout(leftColumn)
        layoutTop.addSpacing(20)
        layoutTop.addWidget(self._creditsWidget)

        layoutTop.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.addStretch()
        layout.addLayout(layoutTop)
        layout.addSpacing(20)
        layout.addWidget(self._buttonBox, 0, QtCore.Qt.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)

        # Center the columns
        self.setContentsMargins(20, 20, 20, 20)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """
        Handles the show event.
        """
        self._buttonBox.setFocus()
        super().showEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Handles the key press event.
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Handles the close event.
        """
        self._buttonBox.setFocus()
        super().closeEvent(event)

    def _initializeCredits(self) -> QtWidgets.QWidget:
        """
        Initializes the credits widget.
        """
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel | QtWidgets.QFrame.Shadow.Sunken)
        widget.setLineWidth(1)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(2)

        layout.addStretch()
        for credit in credits:
            if isinstance(credit, Title):
                layout.addSpacing(10)
                layout.addWidget(self._createTitle(credit))
            elif isinstance(credit, Line):
                layout.addWidget(self._createLine(credit))
            else:
                layout.addWidget(QtWidgets.QLabel(str(credit)))
        layout.addSpacing(10)

        logosLayout = QtWidgets.QHBoxLayout()
        logosLayout.setContentsMargins(0, 0, 0, 0)
        logosLayout.setSpacing(0)
        for logo in logos:
            label = QtWidgets.QLabel()
            label.setPixmap(QtGui.QPixmap(logo))
            label.setAlignment(QtCore.Qt.AlignCenter)
            logosLayout.addWidget(label)

        layout.addLayout(logosLayout)
        layout.addStretch()
        widget.setLayout(layout)

        return widget

    def _createTitle(self, obj: Title) -> QtWidgets.QLabel:
        """
        Creates a title.
        """
        label = QtWidgets.QLabel(obj.text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Weight.Bold))
        return label

    def _createLine(self, obj: Line) -> QtWidgets.QLabel:
        """
        Creates a person.
        """
        if obj.name:
            if obj.username:
                str = f"{obj.name} (<a href=\"{obj.link}\">{obj.username}</a>)" if obj.link else f"{obj.name} ({obj.username})"
            else:
                str = f"<a href=\"{obj.link}\">{obj.name}</a>" if obj.link else obj.name
        else:
            if obj.username:
                str = f"<a href=\"{obj.link}\">{obj.username}</a>" if obj.link else obj.username
            else:
                str = f"<a href=\"{obj.link}\">{obj.link}</a>" if obj.link else ""

        if obj.username and obj.link:
            str = f"{obj.name} (<a href=\"{obj.link}\">{obj.username}</a>)"
        elif obj.username:
            str = f"{obj.name} ({obj.username})"
        elif obj.name:
            str = obj.name

        label = QtWidgets.QLabel(str)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(QtGui.QFont("Segoe UI", 10))
        label.setOpenExternalLinks(True)
        return label
