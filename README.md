
![Phantom Desktop Logo](./docs/banner.png)

[![Build](https://github.com/jhm-ciberman/phantom-desktop/actions/workflows/build.yaml/badge.svg?branch=master)](https://github.com/jhm-ciberman/phantom-desktop/actions/workflows/build.yaml)
![For Windows](https://img.shields.io/badge/for-Windows-blue)
![For Linux](https://img.shields.io/badge/for-Linux-blue)
![Language English](https://img.shields.io/badge/language-English-red)
![Language Spanish](https://img.shields.io/badge/language-Spanish-red)

Phantom Desktop is an application for forensic digital image processing.

![Main screen](./docs/main-screen.jpg)

## Download

Phantom Desktop can be downloaded from the [releases](https://github.com/jhm-ciberman/phantom-desktop/releases) section. The application is available for Windows and Linux. The first time you run the application, it will download the necessary files. After that, you can use it offline.

**IMPORTANT: Requires a CPU that supports AVX Instructions (Any modern CPU > 2011) otherwise the application won't even start.**
If you want to use it on an older CPU, you can need to compile it from source.

Releases were tested in Windows 10 and Ubuntu 22.04 LTS.

## Wiki

The [wiki](https://github.com/jhm-ciberman/phantom-desktop/wiki) contains information about the application and how to use it.

## Contributing
### Initial setup:

After cloning, create a virtual environment, activate it, and install the pip requirements:

```bash
git clone git@github.com:jhm-ciberman/phantom-desktop.git
cd phantom-desktop
python -m venv .env
source .env/Scripts/activate
pip install -r requirements.txt
```

### Running

To run Phantom Desktop from the command line, use the following command:

```bash
python main.py
```

Or in VSCode, you can use the "Run" command, it's already configured for this project in the launch.json file.

### Building

To generate an executable file that can be distributed, run the following command:

```bash
python setup.py build
```

This will use [cx_Freeze](https://cx-freeze.readthedocs.io/en/latest/) to generate an executable file according to the current operating system. The output files will be placed in the `build` folder ready to be distributed.

### Code conventions

This project uses Qt and thus, it tries to follow the Qt style for all classes that inherit from `QObject`. The rest of the code follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide.

For more info please refer to [this](http://bitesofcode.blogspot.com/2011/10/pyqt-coding-style-guidelines.html) blog post.

For Docstrings, the project uses the [Google style](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings).

The project has some type hints, but it's only for basic IDE autocomplete. It's not intended for use with static type checkers.

## Phantom Project File format

The phantom project file format (`*.phantom`) is an open format and it's specification can be found [here](./docs/phantom_project_file_format.md).