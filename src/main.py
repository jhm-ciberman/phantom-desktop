import sys
from PySide6 import QtGui, QtCore, QtWidgets
from MainWindow import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    app.style = QtWidgets.QStyleFactory.create("Fusion")
    #app.setStyleSheet(qdarktheme.load_stylesheet("light"))
    p = app.palette()
    p.setColor(QtGui.QPalette.Window, QtCore.Qt.white)
    app.setPalette(p)

    # app.setStyle(QStyleFactory.create("Fusion"))
    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())
