from cx_Freeze import setup, Executable
import sys

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {
    'packages': [
        "scipy.optimize",
        "scipy.integrate",
    ],
    'excludes': [],
    "include_files": [
        "models/",
        "res/",
    ],
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        './main.py',
        base=base,
        target_name='Phantom',
        icon='./res/icon.ico',
    )
]

setup(name='Phantom Desktop',
      version='1.0',
      description='A desktop application for forensic digital image processing',
      options={'build_exe': build_options},
      executables=executables)
