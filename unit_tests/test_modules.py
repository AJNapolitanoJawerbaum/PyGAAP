import unittest
from sys import path as sys_path
from os import getcwd
from tkinter import *
from pathlib import Path
sys_path.append(getcwd())

from random import randint, choice


class modules(unittest.TestCase): ...

if __name__ == "__main__":
	unittest.main()

