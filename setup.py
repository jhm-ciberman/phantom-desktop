import sys

from cx_Freeze import Executable, setup
import src.constants as constants

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {
    'packages': [
        # scypy is used by sklearn
        "scipy.optimize",
        "scipy.integrate",
    ],
    "include_files": [
        "res/",
    ],
    "bin_includes": [
        "liblapack.so.3",
    ],
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        './main.py',
        base=base,
        target_name='Phantom',
        icon='./res/img/icon.ico',
    )
]

setup(
    name=constants.app_name,
    version=constants.app_version,
    description=constants.app_description,
    options={'build_exe': build_options},
    executables=executables)
