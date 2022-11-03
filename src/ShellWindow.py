from PySide6 import QtCore, QtGui, QtWidgets

from .LanguageWindow import LanguageWindow
from .Application import Application
from .l10n import __
from .Models import Image
from .Workspace import BatchProgress
from .Main.AboutWindow import AboutWindow
from . import constants


class MainMenuBar(QtWidgets.QMenuBar):

    _customMenus: list[QtWidgets.QMenu] = []

    _selectedImages: list[Image] = []

    def __init__(self, parent=None):
        super().__init__(parent)

        self.newProjectAction = QtGui.QAction(
            QtGui.QIcon("res/img/new_project.png"), __("New Project"), self)
        self.newProjectAction.setShortcut("Ctrl+N")
        self.newProjectAction.triggered.connect(self._onNewProjectPressed)

        self.openProjectAction = QtGui.QAction(
            QtGui.QIcon("res/img/folder.png"), __("Open Project..."), self)
        self.openProjectAction.setShortcut("Ctrl+O")
        self.openProjectAction.triggered.connect(self._onOpenProjectPressed)

        self.saveProjectAction = QtGui.QAction(
            QtGui.QIcon("res/img/save.png"), __("Save Project..."), self)
        self.saveProjectAction.setEnabled(False)
        self.saveProjectAction.setShortcut("Ctrl+S")
        self.saveProjectAction.triggered.connect(self._onSaveProjectPressed)

        self.saveProjectAsAction = QtGui.QAction(
            QtGui.QIcon("res/img/save_as.png"), __("Save Project As..."), self)
        self.saveProjectAsAction.setShortcut("Ctrl+Shift+S")
        self.saveProjectAsAction.triggered.connect(self._onSaveProjectAsPressed)

        self.exitAction = QtGui.QAction(
            QtGui.QIcon("res/img/exit.png"), __("Exit"), self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(self._onExitPressed)

        self.addImagesAction = QtGui.QAction(
            QtGui.QIcon("res/img/image_add.png"), __("Add Images..."), self)
        self.addImagesAction.setToolTip(__("Add images to current project"))
        self.addImagesAction.triggered.connect(self._onAddImagesPressed)

        self.addFolderAction = QtGui.QAction(
            QtGui.QIcon("res/img/folder_add.png"), __("Add From Folder..."), self)
        self.addFolderAction.setToolTip(__("Add images from folder to current project"))
        self.addFolderAction.triggered.connect(self._onAddFolderPressed)

        self.exportImageAction = QtGui.QAction(
            QtGui.QIcon("res/img/image_save.png"), __("Export Image..."), self)
        self.exportImageAction.setEnabled(False)
        self.exportImageAction.triggered.connect(self._onExportImagePressed)

        self._fileMenu = self.addMenu(__("@menubar.file.header"))
        self._fileMenu.addAction(self.newProjectAction)
        self._fileMenu.addAction(self.openProjectAction)
        self._fileMenu.addAction(self.saveProjectAction)
        self._fileMenu.addAction(self.saveProjectAsAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self.addImagesAction)
        self._fileMenu.addAction(self.addFolderAction)
        self._fileMenu.addAction(self.exportImageAction)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction(self.exitAction)

        self._settingsMenu = self.addMenu(__("@menubar.settings.header"))
        self._settingsMenu.addAction(__("@menubar.settings.language"), self._onLanguagePressed)

        self._helpMenu = self.addMenu(__("@menubar.help.header"))
        self._helpMenu.addAction(__("@menubar.help.report_issue"), self._onReportIssuePressed)
        self._helpMenu.addAction(__("@menubar.help.documentation"), self._onDocumentationPressed)
        self._helpMenu.addAction(QtGui.QIcon("res/img/github.png"), __("@menubar.help.github"), self._onGithubPressed)
        self._helpMenu.addSeparator()
        self._helpMenu.addAction(__("@menubar.help.about"), self._onAboutPressed)

        Application.workspace().isDirtyChanged.connect(self._onIsDirtyChanged)

    @QtCore.Slot(bool)
    def _onIsDirtyChanged(self, isDirty: bool) -> None:
        self.saveProjectAction.setEnabled(isDirty)

    @QtCore.Slot()
    def _onOpenProjectPressed(self) -> None:
        Application.projectManager().openProject(self)

    @QtCore.Slot()
    def _onNewProjectPressed(self) -> None:
        Application.projectManager().newProject(self)

    @QtCore.Slot()
    def _onSaveProjectPressed(self) -> None:
        Application.projectManager().saveProject(self)

    @QtCore.Slot()
    def _onSaveProjectAsPressed(self) -> None:
        Application.projectManager().saveProjectAs(self)

    @QtCore.Slot()
    def _onAddImagesPressed(self) -> None:
        Application.projectManager().importImages(self)

    @QtCore.Slot()
    def _onAddFolderPressed(self) -> None:
        Application.projectManager().addFolder(self)

    @QtCore.Slot()
    def _onExportImagePressed(self) -> None:
        if len(self._selectedImages) != 0:
            Application.projectManager().exportImages(self, self._selectedImages)

    @QtCore.Slot()
    def _onExitPressed(self) -> None:
        Application.exit()

    @QtCore.Slot()
    def _onAboutPressed(self) -> None:
        AboutWindow().exec()

    @QtCore.Slot()
    def _onDocumentationPressed(self) -> None:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(constants.app_docs_url))

    @QtCore.Slot()
    def _onReportIssuePressed(self) -> None:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(constants.app_bugs_url))

    @QtCore.Slot()
    def _onGithubPressed(self) -> None:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(constants.app_repo_url))

    @QtCore.Slot()
    def _onLanguagePressed(self) -> None:
        LanguageWindow(self, needsRestart=True).exec()

    def clearCustomMenus(self) -> None:
        for menu in self._customMenus:
            self.removeAction(menu.menuAction())
        self._customMenus.clear()

    def addCustomMenu(self, menu: QtWidgets.QMenu) -> None:
        # Menus are added before the settings menu
        self.insertMenu(self._settingsMenu.menuAction(), menu)
        self._customMenus.append(menu)

    def selectedImages(self) -> list[Image]:
        return self._selectedImages

    def setSelectedImages(self, images: list[Image]) -> None:
        self._selectedImages = images
        self.exportImageAction.setEnabled(len(images) != 0)


class NavigationPage:
    """
    A interrface class that defines a page that can be shown in the ShellWindow in the main tab widget.
    """

    def customMenus(self) -> list[QtWidgets.QMenu]:
        """
        Returns a list of custom menus that should be added to the menu bar. These menus will be added
        to the menu bar and only shown when this page is active.
        """
        return []


class ShellWindow(QtWidgets.QMainWindow):
    """
    The main window of the application. It displays the toolbars and a tab widget.
    """

    _currentPage: QtWidgets.QWidget = None

    _mainPage: QtWidgets.QWidget = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self._initUI()

    def _initUI(self):
        self.setWindowTitle(constants.app_name)
        self.setWindowIcon(Application.instance().icon())
        self.setMinimumSize(800, 600)

        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().setFixedHeight(20)

        self._progressBar = QtWidgets.QProgressBar()
        self._progressBar.setFixedHeight(20)
        self._progressBar.setFixedWidth(200)
        self._progressBar.setValue(0)
        self._progressBar.setVisible(False)
        self._progressBar.setTextVisible(False)
        self.statusBar().addPermanentWidget(self._progressBar)

        self._tabWidget = QtWidgets.QTabWidget()
        self._tabWidget.setTabsClosable(True)  # We need to hide the close button for the main page
        self._tabWidget.setIconSize(QtCore.QSize(24, 24))
        self.setCentralWidget(self._tabWidget)
        self._tabWidget.currentChanged.connect(self._onTabChanged)
        self._tabWidget.tabCloseRequested.connect(self._onTabCloseRequested)

        self._menuBar = MainMenuBar(self)
        self.setMenuBar(self._menuBar)
        Application.workspace().batchProgressChanged.connect(self._onBatchProgressChanged)
        Application.workspace().isDirtyChanged.connect(self._onIsDirtyChanged)
        Application.workspace().projectChanged.connect(self._onProjectChanged)

        from .Main.ProjectExplorerPage import ProjectExplorerPage
        self._mainPage = ProjectExplorerPage(self)
        self.openPage(self._mainPage)
        self._hideCloseButtonForTab(index=0)

    @QtCore.Slot(BatchProgress)
    def _onBatchProgressChanged(self, batch: BatchProgress) -> None:
        self._progressBar.setValue(batch.progress * 100)

        if batch.total == 0:
            self._progressBar.setVisible(False)
            pass
        elif batch.value == batch.total:
            self._progressBar.setVisible(False)
            self.statusBar().showMessage(__("Processing finished"))
        else:
            self.statusBar().showMessage(__("Processing images {current}/{total}", current=batch.value, total=batch.total))
            self._progressBar.setVisible(True)

    @QtCore.Slot(bool)
    def _onIsDirtyChanged(self, isDirty: bool) -> None:
        self._updateWindowTitle()

    @QtCore.Slot()
    def _onProjectChanged(self) -> None:
        self._updateWindowTitle()

    def _updateWindowTitle(self) -> None:
        project = Application.workspace().project()
        dirtyDot = "*" if Application.workspace().isDirty() else ""
        appName = Application.applicationName()
        self.setWindowTitle(f"{project.name}{dirtyDot} - {appName}")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if not Application.projectManager().closeProject(self):
            event.ignore()
            return

        super().closeEvent(event)

    @QtCore.Slot(int)
    def _onTabChanged(self, index: int) -> None:
        if index == -1:
            self._currentPage = None
            return

        widget: QtWidgets.QWidget = self._tabWidget.widget(index)
        self._currentPage = widget

        self._menuBar.clearCustomMenus()
        if isinstance(widget, NavigationPage):
            for menu in widget.customMenus():
                self._menuBar.addCustomMenu(menu)

    def openPage(self, page: QtWidgets.QWidget) -> None:
        """
        Adds a page to the tab widget.
        """
        index = self._tabWidget.addTab(page, page.windowIcon(), page.windowTitle())
        self._tabWidget.setCurrentIndex(index)

    def closePage(self, page: QtWidgets.QWidget) -> None:
        """
        Removes a page from the tab widget.
        """
        index = self._tabWidget.indexOf(page)
        if index != -1:
            self._tabWidget.removeTab(index)

    def pageIndex(self, type: type[QtWidgets.QWidget]) -> int:
        """
        Returns the index of the page with the given type or -1 if no page with the given type is open.
        """
        for i in range(self._tabWidget.count()):
            if isinstance(self._tabWidget.widget(i), type):
                return i

        return -1

    def displayPageAtIndex(self, index: int) -> None:
        """
        Displays the page at the given index.
        """
        self._tabWidget.setCurrentIndex(index)

    @QtCore.Slot(int)
    def _onTabCloseRequested(self, index: int) -> None:
        page: NavigationPage = self._tabWidget.widget(index)
        if page == self._mainPage:  # We don't want to close the main page
            return

        self.closePage(page)

    def _hideCloseButtonForTab(self, index: int) -> None:
        """
        Hides the close button for the tab at the given index.
        """
        self._tabWidget.tabBar().setTabButton(index, QtWidgets.QTabBar.RightSide, None)

    def currentPage(self) -> NavigationPage:
        return self._currentPage

    def mainPage(self) -> NavigationPage:
        return self._mainPage

    def setSelectedImages(self, selectedImages: list[Image]) -> None:
        self._menuBar.setSelectedImages(selectedImages)

        count = len(selectedImages)
        if (count == 0):
            totalInProject = len(Application.workspace().project().images)
            self.statusBar().showMessage(__("{count} images in the collection", count=totalInProject))
        elif (count == 1):
            self.statusBar().showMessage(selectedImages[0].path)
        else:
            self.statusBar().showMessage(__("{count} images selected", count=count))
