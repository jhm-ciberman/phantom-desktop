# Phantom Desktop 

A desktop application for forensic digital image processing.

Initial setup:

```bash
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

To run: 

```bash
python src/main.py
```

Or in VSCode, you can use the "Run" command, it's already configured for this project in the launch.json file.

# Build

To generate an executable file that can be distributed, run the following command:

```bash
python setup.py build
```

This will use `cx_Freeze` to generate an executable file according to the current operating system. The output file will be placed in the `build` folder.