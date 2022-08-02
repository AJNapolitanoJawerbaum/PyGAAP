#!/usr/bin/env python3
import sys

from backend.CLI import cliMain
from Constants import version

def main():
	if len(sys.argv) >= 2:	
		print("PyGAAP v" + version + "\nby David Berdik & Michael Fang")
		cliMain()
	else:
		# import backend.GUI.GUI
		from backend.GUI import GUI2
		app = GUI2.PyGAAP_GUI()
		app.run()

if __name__ == "__main__":
	main()