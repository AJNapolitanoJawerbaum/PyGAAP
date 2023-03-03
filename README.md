# Python Graphical Authorship Attribution Program
The Python Graphical Authorship Attribution Program (PyGAAP) is an experimental reimplementation of the [Duquesne University Evaluating Variations in Language Lab's JGAAP](https://github.com/evllabs/JGAAP). Currently, PyGAAP is in early development. Although participation in the development and testing of PyGAAP is encouraged, it is not ready for actual text analysis. **For the latest updates to the code, please see the ```developing``` branch.**


## Features
PyGAAP currently contains only some of the features from JGAAP. Those yet to be implemented include:
* Many of the text and analysis modules
* Extensive logging

## How to Contribute
To contribute to PyGAAP, simply fork the repository, create a new branch, make your desired changes, and submit a pull request. While adding a new module, you may find the [developer manual](/Developer_Manual.md) useful. Additionally, please consider opening an issue on this repository with an explanation of your planned contribution so that we may track who is working on what.

## How to Use
1. Clone the PyGAAP Git repository.
2. Install Python 3. Depending on your Operating System, it may already be installed.
3. Install the Python libraries required by PyGAAP. If you use pip, you can easily install the required libraries by executing one of the following commands from the root PyGAAP directory:
    1. `pip install -r requirements.txt`.
    2. `python -m pip install -r requirements.txt`
	3. `pip3 install -r requirements.txt`
    4. `python3 -m pip install -r requirements.txt`
4. Run `python PyGAAP.py` to launch the PyGAAP GUI. Alternatively, PyGAAP can be executed on command line as well. Run `python PyGAAP.py -h` to print the command line help.

## Support
If you are having issues with PyGAAP that require support, please open an issue on this repository. As a reminder, PyGAAP is in early stages of development and should not be used for serious text analysis. If you require stable text analysis software, please use [JGAAP](https://github.com/evllabs/JGAAP) instead.

---
![PyGAAP](res/logo.png)