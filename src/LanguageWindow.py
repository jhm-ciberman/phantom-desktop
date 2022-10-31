from PySide6 import QtCore, QtWidgets
from .Main.PhantomMascotAnimationWidget import PhantomMascotLangAnimation
from .SettingsService import SettingsService
from .l10n import Language, LocalizationService, __


class LanguageWindow(QtWidgets.QDialog):
    """
    A small popup window that let the user select a language. The language is retrieved
    from the LocalizationService.get_languages() and saved with the SettingsService.
    """

    def __init__(self, parent: QtWidgets.QWidget = None, needsRestart: bool = True):
        """
        Creates a new instance of the LanguageSelector.
        """
        super().__init__(parent)

        self._needsRestart = needsRestart
        self._settings = SettingsService.instance()
        self._languages: list[Language] = LocalizationService.instance().get_languages()
        self._originalLanguage = LocalizationService.instance().get_language()

        # Can be closed
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle(QtWidgets.QApplication.applicationName())
        self.setContentsMargins(20, 20, 20, 20)

        self._label = QtWidgets.QLabel(self)
        self._label.setText(__("@language_selector.label"))

        self._combo = QtWidgets.QComboBox(self)
        self._combo.addItems([language.name for language in self._languages])
        self._combo.setMinimumWidth(200)

        self._acceptButton = QtWidgets.QPushButton(self)
        self._acceptButton.clicked.connect(self._onAcceptPressed)
        self._acceptButton.setText(__("@language_selector.accept"))

        self._animation = PhantomMascotLangAnimation(self)

        columnLayout = QtWidgets.QVBoxLayout()
        columnLayout.setSpacing(20)
        columnLayout.addStretch()
        columnLayout.addWidget(self._label)
        columnLayout.addWidget(self._combo)
        columnLayout.addWidget(self._acceptButton)
        columnLayout.addStretch()

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(20)
        layout.addLayout(columnLayout)
        layout.addWidget(self._animation)
        self.setLayout(layout)

        for i, language in enumerate(self._languages):
            if language.code == self._originalLanguage:
                self._combo.setCurrentIndex(i)
                break

    def _onAcceptPressed(self):
        currentLang = self._languages[self._combo.currentIndex()].code
        self._settings.set("language", currentLang)

        if currentLang != self._originalLanguage:
            if self._needsRestart:
                QtWidgets.QMessageBox.information(
                    self,
                    __("@language_selector.restart.title"),
                    __("@language_selector.restart.message"),
                )
            else:
                LocalizationService.instance().set_locale(currentLang)

        self.accept()
