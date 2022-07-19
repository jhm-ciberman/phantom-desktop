# Phantom Desktop 

A desktop application for forensic digital image processing.

## Initial setup:

Phantom desktop uses git submodules, so you need to clone the repository and then initialize the submodules:

```bash
git clone git@github.com:jhm-ciberman/phantom-desktop.git
git submodule update --init --recursive
```

After that, create a virtual environment, activate it, and install the pip requirements:

```bash
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

## Running

To run Phantom Desktop from the command line, use the following command:

```bash
python src/main.py
```

Or in VSCode, you can use the "Run" command, it's already configured for this project in the launch.json file.

## Building

To generate an executable file that can be distributed, run the following command:

```bash
python setup.py build
```

This will use `cx_Freeze` to generate an executable file according to the current operating system. The output file will be placed in the `build` folder.