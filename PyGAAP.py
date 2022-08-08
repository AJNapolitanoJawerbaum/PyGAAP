#!/usr/bin/env python3
import sys
from Constants import version, versiondate

def main():
	if len(sys.argv) >= 2:
		from backend.CLI import cliMain
		print("PyGAAP v" + version + " (CLI, " + versiondate + ")\nby David Berdik & Michael Fang\n")
		cliMain()
	else:
		# import backend.GUI.GUI
		from backend.GUI import GUI2
		#app = GUI2.PyGAAP_GUI()
		app = GUI2.PyGAAP_GUI()
		app.run()

if __name__ == "__main__":
	main()