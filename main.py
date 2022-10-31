import sys
from multiprocessing import freeze_support

from src.Application import Application

if __name__ == "__main__":
    # This line is to add multiprocessing support.
    # On Windows, if you don't have this line, you'll get
    # multiple copies of your app running. (Multiple windows will open)
    # See https://docs.python.org/dev/library/multiprocessing.html#multiprocessing.freeze_support
    freeze_support()

    # Now we can run the app
    app = Application(sys.argv)
    app.exec()
