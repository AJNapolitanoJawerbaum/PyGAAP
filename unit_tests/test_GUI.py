import unittest
from sys import path as sys_path
from os import getcwd
from tkinter import *
from pathlib import Path
sys_path.append(getcwd())

from random import randint, choice

from backend.GUI.GUI2 import PyGAAP_GUI

app = PyGAAP_GUI()
app.test_run


class testing_GUI(unittest.TestCase):




	def test_unknown_authors(self):
		app = PyGAAP_GUI()
		app.test_run()
		app._edit_unknown_docs("add", test=True, add_list=(getcwd()+"/resources/aaac/problemA/Asample01.txt"))
		self.assertEqual(app.Tab_Documents_UnknownAuthors_listbox.get(0, END), (getcwd()+'/resources/aaac/problemA/Asample01.txt',))
		self.assertEqual([d.filepath for d in app.backend_API.unknown_docs], [getcwd()+'/resources/aaac/problemA/Asample01.txt',])
		app._edit_unknown_docs("add", test=True, add_list=(getcwd()+"/resources/aaac/problemA/Asample02.txt"))
		self.assertEqual(app.Tab_Documents_UnknownAuthors_listbox.get(0, END), (getcwd()+"/resources/aaac/problemA/Asample01.txt", getcwd()+"/resources/aaac/problemA/Asample02.txt"))
		self.assertEqual([d.filepath for d in app.backend_API.unknown_docs], [getcwd()+"/resources/aaac/problemA/Asample01.txt", getcwd()+"/resources/aaac/problemA/Asample02.txt"])
		app._edit_unknown_docs("clear")
		self.assertEqual(app.Tab_Documents_UnknownAuthors_listbox.get(0, END), ())
		self.assertEqual(len(app.backend_API.unknown_docs), 0)


		print("unknown authors: chain add/chain random remove")
		# without using auto-add
		add_list = list()
		for i in range(1, 7):
			add_string = getcwd()+"/resources/aaac/problemA/Asample0%s.txt" % str(i)
			add_list.append(add_string)
			app._edit_unknown_docs("add", test=True, add_list=(add_string))

		for i in range(1, 20):
			if i >= 10: add_string = getcwd()+"/resources/aaac/problemM/Msample%s.txt" % str(i)
			else: add_string = getcwd()+"/resources/aaac/problemM/Msample0%s.txt" % str(i)
			add_list.append(add_string)
			app._edit_unknown_docs("add", test=True, add_list=(add_string))

		self.assertEqual(app.Tab_Documents_UnknownAuthors_listbox.get(0, END), tuple(add_list))
		self.assertEqual([d.filepath for d in app.backend_API.unknown_docs], add_list)
		self.assertEqual([d.author for d in app.backend_API.unknown_docs], ["" for x in add_list])

		for i in range(0, len(add_list)-3):
			rand_select = randint(0, len(add_list)-1)

			add_list.pop(rand_select)
			# simulate cursor selection
			app.Tab_Documents_UnknownAuthors_listbox.select_clear(0, END)
			app.Tab_Documents_UnknownAuthors_listbox.select_set(rand_select)
			app._edit_unknown_docs("remove")
			self.assertEqual(app.Tab_Documents_UnknownAuthors_listbox.get(0, END), tuple(add_list))
			self.assertEqual([d.filepath for d in app.backend_API.unknown_docs], add_list)
		print()

		app._edit_unknown_docs("remove")
		return
	
	def test_known_authors(self): ...

	def _listboxes_test(self): ...

	def test_find_parameters(self): ...


# if __name__ == "__main__":
# 	from backend.GUI.GUI2 import PyGAAP_GUI
# 	app = PyGAAP_GUI()
# 	app.test_run()
# 	unittest.main()

if __name__ == "__main__":
	app = PyGAAP_GUI()
	app.test_run()
	app.switch_tabs(app.tabs, "choose", 6)
	print(app.Tab_RP_Process_Button["state"])

