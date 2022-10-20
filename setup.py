import sys

from cx_Freeze import Executable, setup

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

setup(name='Phantom Desktop',
      version='1.0',
      description='A desktop application for forensic digital image processing',
      options={'build_exe': build_options},
      executables=executables)
