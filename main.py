import sys
from PySide6 import QtGui, QtCore, QtWidgets
from src.Application import Application

if __name__ == "__main__":
    app = Application(sys.argv)
    app.run()
