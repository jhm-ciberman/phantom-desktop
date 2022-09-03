import sys
from PySide6 import QtGui, QtCore, QtWidgets
from src.MainWindow import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    app.style = QtWidgets.QStyleFactory.create("Fusion")

    p = app.palette()
    p.setColor(QtGui.QPalette.Window, QtCore.Qt.white)
    app.setPalette(p)

    app.setStyleSheet("""
        QWidget { margin:0 px; }
        QLayout { margin:0 px; }
        QStatusBar { background-color: #f0f0f0; }
    """)

    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec())
