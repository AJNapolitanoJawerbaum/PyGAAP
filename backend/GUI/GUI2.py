# PyGAAP is the Python port of JGAAP,
# Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
#
# See PyGAAP_developer_manual.md for a guide to the structure of the GUI
# @ author: Michael Fang
#
# Style note: if-print checks using the GUI_debug variable
# are condensed into one line where possible.

TEST_WIN = False
GUI_debug = 0
# GUI debug level:
#   0 = no debug info.
#   1 = basic status update.
#   3 = most function calls.
#   info printed to the terminal.

# system modules
from copy import deepcopy
from multiprocessing import Process, Queue, Pipe, set_start_method
from datetime import datetime
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from sys import modules as sys_modules
from sys import exc_info
from sys import platform
from json import load as json_load
from json import dump as json_dump
from pickle import dump as pickle_dump
from os import listdir as ls
from time import sleep
from pathlib import Path
from os import getcwd
from gc import collect as collect_garbage
from traceback import format_exc
from idlelib.tooltip import Hovertip

# local modules
from backend.CSVIO import readDocument, readCorpusCSV, readExperimentCSV
import util.MultiprocessLoading as MultiprocessLoading
from backend.Document import Document
from backend import CSVIO
import Constants

# create tabs
from backend.GUI import GUI_unified_tabs

# Windows compatibility
if platform != "win32" and not TEST_WIN:
	from backend import run_experiment
else:
	if __name__ == "backend.GUI.GUI2":
		from backend import API_manager

if TEST_WIN:
	try:
		set_start_method("spawn")
		if platform != "win32": print("Testing using spawn.")
	except RuntimeError: pass
if GUI_debug > 0: print("GUI_debug:", GUI_debug)

def todofunc():
	"""Place-holder function for not-yet implemented features."""
	print("To-do function")
	return

class PyGAAP_GUI:

	# list of parameters
	gui_params = None
	style_choice = "JGAAP_blue"
	backend_API = None

	icon = None

	tabs_names = [
		"Tab_Documents",
		"Tab_Canonicizers",
		"Tab_EventDrivers",
		"Tab_EventCulling",
		"Tab_Embeddings",
		"Tab_AnalysisMethods",
		"Tab_ReviewProcess"
	]
	tabs_frames = dict()

	known_authors: list = []
	# self.backend_API.known_authors list format:
	#   [
	#	   [author, [file-directory, file-directory]],
	#	   [author, [file-directory, file directory]]
	#   ]

	# tkinter StringVars.
	# need to save because need tkinter to detect changes
	search_entry_query = dict()
	search_dictionary = dict()
	tooltips = dict()

	# list of functions
	list_of_functions: dict = {}

	# list of dynamically displayed parameters
	Tab_Canonicizers_parameters_displayed = []
	Tab_EventDrivers_parameters_displayed: list = []
	Tab_EventCulling_parameters_displayed: list = []
	Tab_AnalysisMethods_parameters_displayed: list = []

	# references to lists of GUI items
	generated_widgets: dict = {}

	# References to specific GUI items
	tabs = None
	statusbar = None
	statusbar_label = None
	results_window = None
	about_page = None
	notes_content = ""
	notepad_window = None
	author_window = None

	Tab_Documents_UnknownAuthors_listbox: Listbox = None
	Tab_Documents_KnownAuthors_treeview: ttk.Treeview = None
	Tab_Documents_KnownAuthors_doc_stats = None
	Tab_Documents_UnknownAuthors_doc_stats = None

	Tab_RP_Canonicizers_Listbox: Listbox = None
	Tab_RP_EventDrivers_Listbox: Listbox = None
	Tab_RP_EventCulling_Listbox: Listbox = None
	Tab_RP_AnalysisMethods_Listbox: ttk.Treeview = None
	Tab_RP_Process_Button: Button = None

	progress_window: Toplevel = None
	error_window: Toplevel = None

	list_of_results = [] # [[name-string, results-object], [..., ...], ...]

	def __init__(self):
		# no internal error handling because fatal error.
		with open(Path("./resources/gui_params.json"), "r") as f:
			params = json_load(f)
			self.gui_params = params
			self.gui_params["styles"]["JGAAP_blue"]
			self.backend_API = None

		try:
			f = open(Path("./resources/search_dictionary.json"), "r")
			self.search_dictionary = json_load(f)
			f.close()
		except FileNotFoundError:
			self.search_dictionary = dict()
			print("Search dictionary not found.")

		try:
			with open(Path("./resources/tooltips.json"), "r") as f:
				self.tooltips = json_load(f)
		except FileNotFoundError:
			self.tooltips = dict()
			print("Tooltip data not found.")

		try:
			self.icon = open(self.gui_params["icon"], "r")
		except FileNotFoundError:
			print("Icon not found")

		# self._bottom_frame

		self.list_of_functions ={
			"select_modules": self.select_modules,
			"find_parameters": self.find_parameters,
			"find_description": self.find_description,
			"check_DF_listbox": self.check_DF_listbox,
		}
		return

	def switch_tabs(self, notebook, mode, tabID = 0):
		"""
		Switch tabs from the buttons "Previous", "Next",  and "Finish & Review"
		"""
		# contains hard-coded limits of tabIDs.
		if GUI_debug >= 3: print("self.switch_tabs(mode = %s)" %(mode))
		if mode == "next":
			notebook.select(min((notebook.index(notebook.select()) + 1), 6))
		elif mode == "previous":
			notebook.select(max((notebook.index(notebook.select()) - 1), 0))
		elif mode == "choose":
			if tabID >= 0 and tabID <= 6:
				notebook.select(tabID)
		return

	def show_error_window(self, error_text:str, title="Error"):
		self.error_window = None
		self.error_window = Toplevel()
		self.error_window.geometry(self.dpi_setting["dpi_about_page_geometry"])
		self.error_window.title(title)

		Label(self.error_window, text=error_text).pack(padx=30, pady=30)
		return

	def toggle_mp(self):
		self.backend_API.default_mp = not self.backend_API.default_mp
		print("Built-in multiprocessing:", self.backend_API.default_mp)
		self.status_update("Built-in MP: "+str(self.backend_API.default_mp))
		return

	def run_experiment(self):
		if GUI_debug >= 3: print("run_experiment()")


		am_df_names = [self.Tab_RP_AnalysisMethods_Listbox.item(j)["values"]
						for j in list(self.Tab_RP_AnalysisMethods_Listbox.get_children())]
		# names of modules in use
		module_names = {
			"Canonicizers": list(self.Tab_RP_Canonicizers_Listbox.get(0, END)),
			"EventDrivers": list(self.Tab_RP_EventDrivers_Listbox.get(0, END)),
			"EventCulling": list(self.Tab_RP_EventCulling_Listbox.get(0, END)),
			"Embeddings": list(self.Tab_RP_Embeddings_Listbox.get(0, END)),
			"AnalysisMethods": [x[0] for x in am_df_names],
			"DistanceFunctions": [x[1] for x in am_df_names]
		}

		self.Tab_RP_Process_Button.config(state=DISABLED)
		progress_report_here, progress_report_there = Pipe(duplex=True)

		exp_args = {
			"args": [],
			"kwargs": {"verbose": True}
		}

		if platform != "win32" and not TEST_WIN:
			# linux, mac
			self.results_queue = Queue()

			# this is an instance of the Experiment class
			experiment = run_experiment.Experiment(
				self.backend_API, progress_report_there, self.results_queue,
				dpi=self.dpi_setting,
				default_mp=self.backend_API.default_mp,
			)
			self.experiment_process = Process(
				target=experiment.run_experiment,
				args=exp_args["args"], kwargs=exp_args["kwargs"]
			)
			self.experiment_process.start()
		else:
			# windows
			if platform != "win32": print("Testing using spawn.")
			if __name__ != "backend.GUI.GUI2":
				raise RuntimeError("Process must be called from GUI.")
			self.results_queue = Queue()
			self.pipe_mainproc, self.pipe_subproc = Pipe(duplex=1)
			self.experiment_process = API_manager.manager_run_exp(
				self.backend_API,
				self.pipe_mainproc,
				self.pipe_subproc,
				progress_report_there,
				module_names,
				self.results_queue,
				exp_args=exp_args
			)

		MultiprocessLoading.process_window(
			self.dpi_setting["dpi_process_window_geometry"],
			"determinate",
			progress_report_here,
			starting_text="...",
			progressbar_length=self.dpi_setting["dpi_progress_bar_length"],
			end_run=self.display_results,
			after_user=self.topwindow,
			exp_process=self.experiment_process
		)

		return


	def display_results(self, **options):
		"""Displays results in new window"""
		# show process results
		self.Tab_RP_Process_Button.config(state=NORMAL)
		if options.get("abort", 0): return
		exp_return = self.results_queue.get()
		results_text = exp_return["results_text"]

		if not exp_return["status"]: self.list_of_results.append(exp_return)

		if exp_return["status"] != 0 or exp_return["message"].strip() != "":
			error_window = Toplevel()
			error_window.geometry(self.dpi_setting["dpi_process_window_error"])

			error_text = ""
			if exp_return["status"]:
				error_window.title("Experiment failed")
				error_text += "Experiment failed.\n"
			else:
				error_window.title("Warning")
			error_text += exp_return["message"]
			error_text_field = Text(error_window)
			error_text_field.pack(fill=BOTH, expand=True)
			error_text_field.insert("end", error_text)
			error_text_field.configure(state="disabled")
			error_window.lift
			if exp_return["status"] != 0:
				return

		self.status_update("")
		self.show_results_window(focus_last=1)
		return

	def show_results_window(self, **options):
		try: self.results_window.destroy()
		except AttributeError: pass
		self.results_window = Toplevel()
		self.results_window.title("Experiment results")
		self.results_window.geometry(self.dpi_setting["dpi_process_window_geometry"])
		
		#self.results_window.bind("<Destroy>", lambda event, b = "":self.status_update(b))

		results_tabs = ttk.Notebook(self.results_window)
		results_tabs.grid(row=0, column=0, sticky="swen")

		self.results_window.columnconfigure(0, weight=1)
		self.results_window.rowconfigure(0, weight=1)
		self.results_window.rowconfigure(1, weight=0)


		for output in self.list_of_results:

			if output["message"].strip() == "":
				tab_text = output["exp_time"]
			else:
				tab_text = output["exp_time"] + " [Partial]"

			text_frame = Frame(results_tabs, height=50, width=40)
			results_tabs.add(text_frame, text=tab_text)
			# no pack/grid for frames of notebooks

			results_display = Text(text_frame)
			results_display.pack(fill=BOTH, expand=True, side=LEFT)
			results_display.insert(END, output["results_text"])
			results_display.config(state = DISABLED)

			results_scrollbar = Scrollbar(text_frame,
										width = self.dpi_setting["dpi_scrollbar_width"],
										command = results_display.yview)
			results_display.config(yscrollcommand = results_scrollbar.set)
			results_scrollbar.pack(side = LEFT, fill = BOTH, anchor="nw")

		export_buttons_frame = Frame(self.results_window)
		export_buttons_frame.grid(row=1, column=0, sticky="swen")

		if len(self.list_of_results):
			results_export = Button(
				export_buttons_frame, text="Save this experiment",
				command=lambda tab_obj=results_tabs:
				self.export_exp_results(tab_obj=tab_obj)
			)
			results_export.pack(side=RIGHT)
			clear_results = Button(
				export_buttons_frame, text="Clear history and close",
				command=self.clear_exp_history
			)
			clear_results.pack(side=LEFT)
		else:
			Label(self.results_window, text="No experiments to show.").grid(row=0, column=0)

		self.results_window.geometry(self.dpi_setting["dpi_process_window_geometry_finished"])

		self.change_style(self.results_window)
		if options.get("focus_last", False):
			results_tabs.select(results_tabs.index("end")-1)
		return

	def clear_exp_history(self):
		for i in self.list_of_results: del i
		self.list_of_results = []
		self.results_window.destroy()
		return

	def export_exp_results(self, **options):
		if options.get("tab_obj", False):
			tab_obj = options["tab_obj"]
			results = self.list_of_results[tab_obj.index(tab_obj.select())]
		else: return
		save_to = asksaveasfilename(
			filetypes = (("JavaScript Object Notation", "*.json"), ("Serialized Python Object", "*.pkl"),
				("Text File", "*.txt"), ("Show All Files", "*.*")),
			title = "Save experiment results",
			parent = self.results_window
		)
		if len(save_to) <= 0: return
		elif type(save_to) != str: save_to = save_to[0]
		if save_to.endswith(".json"):
			with open(save_to, "w+") as save_to_file:
				json_dump(results["full_exp_dump"], save_to_file, indent=4)
		elif save_to.endswith(".pkl"):
			with open(save_to, "wb") as save_to_file:
				pickle_dump(results["full_exp_dump"], save_to_file)
		elif save_to.endswith(".txt") or len(save_to.split(".")) == 1:
			# if no extension specified, save as text.
			with open(save_to, "w+") as save_to_file:
				save_to_file.write(results["results_text"])
		else:
			raise ValueError("Unknown file type")
		self.status_update("Saved as %s" % save_to)

	def process_check(
			self,
			check_listboxes: list,
			check_labels: list,
		):
		if GUI_debug >= 3: print("process_check()")
		all_set = True
		# first check if the listboxes in check_listboxes are empty. If empty
		self.Tab_RP_Process_Button.config(state = NORMAL, text = "Process")
		for lb_index in range(len(check_listboxes)):
			try: size = len(check_listboxes[lb_index].get_children())
			except AttributeError: size = check_listboxes[lb_index].size()
			if size == 0:
				check_labels[lb_index].config(
					fg = "#e24444",
					activeforeground = "#e24444")
				self.Tab_RP_Process_Button.config(
					fg = "#333333",
					state = DISABLED,
					text = "Process [missing parameters]",
					activebackground = "light grey", bg = "light grey")
				# if something is missing
			else: # if all is ready
				check_labels[lb_index].config(
					fg = "black", activeforeground = "black",
				)
				self.Tab_RP_Process_Button.config(
					activebackground = self.gui_params["styles"][self.style_choice]["accent_color_mid"],
					bg = self.gui_params["styles"][self.style_choice]["accent_color_mid"]
				)
		self.Tab_RP_Process_Button.config(fg = "black")
		return


	def status_update(self, displayed_text="", ifsame=None):
		"""
		updates the text in the status bar.
		"""
		# ifsame: only update the text
		# if the currently displayed text is the same as this string.
		
		if GUI_debug >= 3:
			print("status_update('%s', condition = %s)"
					%(displayed_text, ifsame))
		if ifsame == None:
			# do not check if the status text is the same as "ifsame"
			if self.statusbar_label['text'] == displayed_text:
				self.statusbar_label.config(text = " ")
				self.topwindow.after(20,
									lambda t = displayed_text:self.status_update(t))
			else: self.statusbar_label.config(text = displayed_text)
		else: # only change label if the text is the same as "ifsame"
			if self.statusbar_label['text'] == ifsame:
				self.statusbar_label.config(text = displayed_text)
		return


	def notepad(self):
		"""Notes button window"""
		# prevents spam-spawning. took me way too long to figure this out
		if GUI_debug >= 3: print("notepad()")
		try:
			self.notepad_window.lift()
		except (NameError, AttributeError, TclError):
			self.notepad_window = Toplevel()
			self.notepad_window.title("Notes")
			#self.notepad_window.geometry("600x500")
			self.notepad_window_textfield = Text(self.notepad_window)
			self.notepad_window_textfield.insert("1.0", str(self.notes_content))
			self.notepad_window_save_button = Button(self.notepad_window, text = "Save & Close",\
				command = lambda:self.notepad_Save(
					self.notepad_window_textfield.get("1.0", "end-1c"),
					self.notepad_window))
			self.notepad_window_textfield.pack(padx = 7, pady = 7, expand = True, fill = BOTH)
			self.notepad_window_save_button.pack(pady = (0, 12), padx = 100, fill = BOTH)
			self.change_style(self.notepad_window)
			self.notepad_window.mainloop()
		return

	def notepad_Save(self, text, window):
		"""
		saves the contents displayed in the notepad textfield
		when the button is pressed
		"""
		self.notes_content = text
		window.destroy()
		if GUI_debug >= 3: print("notepad_Save()")
		return

	def authors_list_updater(self):
		"""This updates the ListBox from the self.backend_API.known_authors python-list"""
		opened_items = dict()
		tv = self.Tab_Documents_KnownAuthors_treeview
		for entry in tv.get_children():
			if tv.item(entry)["open"]:
				opened_items[tv.item(entry)["text"]] = True
		tv.delete(*tv.get_children())
		if GUI_debug >= 3: print("authors_list_updater()")
		for author_list in self.backend_API.known_authors:
			author_node = tv.insert("", "end", text=str(author_list[0]))
			for document in author_list[1]:
				tv.insert(author_node, "end", text=str(document))
		for entry in tv.get_children():
			if opened_items.get(tv.item(entry)["text"], False):
				tv.item(entry, open=True)
		self.Tab_Documents_KnownAuthors_doc_stats["text"] = "Authors: "\
			+ str(len(self.backend_API.known_authors)) + " Docs: " + str(sum([len(x[1]) for x in self.backend_API.known_authors]))
		return

	def author_save(self, author, documents_list, mode, window=None):
		"""
		This saves author when adding/editing to the self.backend_API.known_authors list.
		Then uses authors_list_updater to update the listbox
		"""

		#Listbox: the authors listbox.
		#author: 
		#	   "ADD MODE": the author's name entered in edit_known_authors window
		#	   "EDIT MODE": [original author name, changed author name]
		#documents_list: list of documents entered in the listbox in the edit_known_authors window
		#mode: add or edit

		if GUI_debug >= 3:
			print("author_save(mode = %s)" %(mode))
			print("author", author, "doc list", documents_list)
		if mode == "add":
			if (author != None and author.strip() != "") \
					and (documents_list != None \
					and len(documents_list) != 0):  
				author_index = 0
				while author_index < len(self.backend_API.known_authors):
					#check if author already exists
					if self.backend_API.known_authors[author_index][0] == author:
						#when author is already in the list, merge.
						self.backend_API.known_authors[author_index][1] = \
							self.backend_API.known_authors[author_index][1] \
							+ list([doc for doc in documents_list
								if doc not in self.backend_API.known_authors[author_index][1]])
						self.authors_list_updater()
						if window != None: window.destroy()
						return
					author_index += 1
				self.backend_API.known_authors += [[author, list(\
									[file for file in documents_list if type(file) == str]
									)]]
									#no existing author found, add.
				self.authors_list_updater()
			if window != None: window.destroy()
			return
		elif mode == 'edit':
			if (author[1] != None \
					and author[1].strip() != "") \
					and (documents_list != None \
					and len(documents_list) != 0):
				author_index = 0
				while author_index<len(self.backend_API.known_authors):
					if self.backend_API.known_authors[author_index][0] == author[0]:
						self.backend_API.known_authors[author_index] = [author[1], documents_list]
						self.authors_list_updater()
						if window != None: window.destroy()
						return
					author_index += 1
				print("Bug: editing author: "
					+ "list of authors and documents changed unexpectedly when saving")
				return
		else:
			print("Bug: unknown parameter passed to 'author_save' function: ",
				str(mode))
		if window != None: window.destroy()
		return


	def edit_known_authors(self, mode):
		"""Add, edit or remove authors
		This opens a window to add/edit authors; does not open a window to remove authors.
			calls author_save (which calls authorListUpdater) when adding/editing author,
		This updates the global self.backend_API.known_authors list.
		"""
		#authorList: the listbox that displays known authors in the topwindow.
		tv = self.Tab_Documents_KnownAuthors_treeview
		if GUI_debug >= 3: print("edit_known_authors(mode = %s)"%(mode))
		if mode == "add":
			title = "Add Author"
		elif mode == 'edit':
			if len(tv.selection()) == 1:
				title = "Edit Author"
				# assumes treeview only has two levels: treeview -> authors -> texts.
				author_index = tv.index(tv.selection()) if tv.parent(tv.selection()) == "" else tv.index(tv.parent(tv.selection()))
				insert_author = self.backend_API.known_authors[author_index][0] #original author name
				insert_docs = self.backend_API.known_authors[author_index][1] #original list of documents
			else:
				self.status_update("Select only one item")
				if GUI_debug > 0:
					print("edit author: selected multiple or zero.")
				return
			# not returning here because it's edit mode, need to open a window.
		elif mode == "remove":#remove author does not open a window
			if len(tv.selection()) == 1 and tv.parent(tv.selection()) == "":
				author_index = tv.index(tv.selection())
				self.backend_API.known_authors.pop(author_index)
				self.authors_list_updater()
			elif len(tv.selection()) == 0:
				self.status_update("No author selected.")
				if GUI_debug > 0:
					print("remove author: nothing selected")
				return
			elif tv.parent(tv.selection()) != "":
				self.status_update("Select an author. To add/remove documents, press Edit")
				print("remove author: Select an author. To add/remove documents, press Edit.")
				return
			return
		elif mode == "clear":
			# self.Tab_Documents_KnownAuthors_treeview.delete(*self.Tab_Documents_KnownAuthors_treeview.get_children())
			self.backend_API.known_authors = []
			self.authors_list_updater()
			return
		else:
			assert mode == "add" or mode == "remove" or mode == "edit", \
				"bug: Internal function 'edit_known_authors' has an unknown mode parameter " \
				+ str(mode)
			return
		try:
			self.author_window.lift()
			return
		except (NameError, AttributeError, TclError):
			pass
		
		self.author_window = Toplevel()
		self.author_window.grab_set()#Disables main window when the add/edit author window appears
		self.author_window.title(title)
		self.author_window.geometry(self.dpi_setting["dpi_author_window_geometry"])
		
		self.author_window.rowconfigure(1, weight = 1)
		self.author_window.columnconfigure(1, weight = 1)

		Label(self.author_window, text = "Author",font = "bold", padx = 10)\
			.grid(row = 0, column = 0, pady = 7, sticky = "NW")
		Label(self.author_window, text = "Files", font = "bold", padx = 10)\
			.grid(row = 1, column = 0, pady = 7, sticky = "NW")

		author_name_entry = Entry(self.author_window, width = 40)
		if mode == "edit":
			author_name_entry.insert(END, insert_author)
		author_name_entry.grid(row = 0, column = 1, pady = 7, sticky = "swen", padx = (0, 10))

		author_listbox = Listbox(self.author_window, height = 12, width = 60)
		if mode == "edit":
			for j in insert_docs:
				author_listbox.insert(END, j)
		author_listbox.grid(row = 1, column = 1, sticky = "swen", padx = (0, 10))

		author_buttons_frame = Frame(self.author_window)
		
		author_add_doc_button = Button(author_buttons_frame, text = "Add Document",\
			command = lambda:self.file_add_remove("Add Document For Author", author_listbox, False, "add", self.author_window))
		author_add_doc_button.grid(row = 0, column = 0)
		author_remove_doc_button = Button(author_buttons_frame, text = "Remove Document",\
			command = lambda:self.file_add_remove(None, author_listbox, False, 'remove'))
		author_remove_doc_button.grid(row = 0, column = 1)
		author_buttons_frame.grid(row = 2, column = 1, sticky = 'NW')

		author_bottom_buttons_frame = Frame(self.author_window)
		#OK button functions differently depending on "add" or "edit".
		author_ok_button = Button(author_bottom_buttons_frame, text = "OK",)
		if mode == "add":
			author_ok_button.configure(command
			= lambda:self.author_save(author_name_entry.get(),
									author_listbox.get(0, END),
									mode,
									self.author_window))
		elif mode == "edit":
			author_ok_button.configure(command
			= lambda:self.author_save([insert_author, author_name_entry.get()],
									author_listbox.get(0, END),
									mode,
									self.author_window))

		author_ok_button.grid(row = 0, column = 0, sticky = "W")
		author_cancel_button = Button(author_bottom_buttons_frame, text = "Cancel",
			command = lambda:self.author_window.destroy())
		author_cancel_button.grid(row = 0, column = 1, sticky = "W")
		author_bottom_buttons_frame.grid(row = 3, column = 1, pady = 7, sticky = "NW")	
		self.change_style(self.author_window)

		self.author_window.mainloop()
		return
	
	def load_save_csv(self, function, autoload_corpus_filepath=None):
		"""Batch load or save corpus csv"""
		if "load" in function:
			if "autoload" in function:
				filename = autoload_corpus_filepath
				assert filename != None, "load_save_csv() autoload corpus cannot be empty"
			elif function == "load" or function == "load_clear":
				filename = askopenfilename(
					filetypes = (("Comma separated values", "*.csv"), ("Text File", "*.txt"), ("All Files", "*.*")),
					title = "Load corpus csv", multiple = False
				)
			corpus_list = readCorpusCSV(filename)
			if len(corpus_list) == 0: return
			if "clear" in function:
				self._edit_unknown_docs("clear")
				self.edit_known_authors("clear")
			unknown = [Document(x[0], x[2], "", x[1]) for x in corpus_list if x[0] == ""]
			known = [Document(x[0], x[2], "", x[1]) for x in corpus_list if x[0] != ""] + [Document("", "", "", "")]
			# add unknown docs

			if function == "autoload":
				self._edit_unknown_docs("clear_autoadd", add_list=unknown)
			else:
				self._edit_unknown_docs("autoadd", add_list=unknown)

			# add known docs
			this_author = ""
			this_author_list = []
			for doc in known:
				if doc.author != this_author:
					if this_author != "":
						self.author_save(this_author, this_author_list, "add")
					this_author = doc.author
					this_author_list = [doc.filepath]
				else:
					this_author_list.append(doc.filepath)
			self.status_update("Loaded corpus")
			self.topwindow.after(3000, lambda:self.status_update("", "Loaded corpus"))
			return

		elif function == "save":
			filename = asksaveasfilename(
				filetypes = (("Comma separated values", "*.csv"), ("Text File", "*.txt"), ("All Files", "*.*")),
				title = "Save document list to corpus csv"
			)
			if len(filename) == 0: return
			with open(filename, "w+") as write_to:
				for doc in self.backend_API.unknown_docs:
					filepath = doc.filepath
					if filepath[0] == ".": filepath = getcwd() + filepath[1:]
					elif filepath[0] != "/": filepath = getcwd() + filepath
					write_to.write(","+filepath+","+doc.author+"\n")
				for auth_list in self.backend_API.known_authors:
					for doc in auth_list[1]:
						filepath = doc
						if filepath[0] == ".": filepath = getcwd() + filepath[1:]
						elif filepath[0] != "/": filepath = getcwd() + filepath
						write_to.write(auth_list[0]+","+filepath+","+doc.split("/")[-1]+"\n")
			self.status_update("Saved corpus to %s" % filepath)
			self.topwindow.after(5000, lambda:self.status_update("", ("Saved corpus to %s" % filepath)))
			return


		else: raise ValueError("Unknown parameter for GUI.load_save_csv:", function)

	def load_aaac(self, problem: str):
		"""Loads AAAC problems"""
		# problem: "problem" + capital character.
		corpus_file_path = self.gui_params["aaac_problems_path"]+'problem%s/load%s.csv' % (problem, problem[-1])
		# corpus_list = CSVIO.readCorpusCSV(corpus_file_path)
		if GUI_debug >= 3: print("problem %s" % problem)
		self.load_save_csv("autoloadclear", corpus_file_path)
		return

	def _review_process_tab(self, tabs):
		#####REVIEW & PROCESS TAB
		#basic frames structure
		Tab_ReviewProcess_Canonicizers = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_Canonicizers.grid(
			row = 0, column = 0, sticky = "wens", padx = 10, pady = 10
		)

		Tab_ReviewProcess_EventDrivers = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_EventDrivers.grid(
			row = 0, column = 1, sticky = "wens", padx = 10, pady = 10
		)

		Tab_ReviewProcess_EventCulling = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_EventCulling.grid(
			row = 0, column = 2, sticky = "wens", padx = 10, pady = 10
		)
		
		Tab_ReviewProcess_Embeddings = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_Embeddings.grid(
			row = 1, column = 0, sticky = "wens", padx = 10, pady = 10
		)

		Tab_ReviewProcess_AnalysisMethods = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_AnalysisMethods.grid(
			row = 1, column = 1, sticky = "wens", padx = 10, pady = 10
		)

		for n in range(3):
			self.tabs_frames["Tab_ReviewProcess"].columnconfigure(n, weight = 1)
		for n in range(2):
			self.tabs_frames["Tab_ReviewProcess"].rowconfigure(n, weight = 1)

		# TODO condense RP tab generation.
		#RP = ReviewProcess
		#note: the buttons below (that redirect to corresponding tabs) have hard-coded tab numbers
		Tab_RP_Canonicizers_Button = Button(
			Tab_ReviewProcess_Canonicizers,  text = "Canonicizers", font = ("helvetica", 16), relief = FLAT,
			command = lambda:self.switch_tabs(tabs, "choose", 1), activeforeground = "#333333")
		Tab_RP_Canonicizers_Button.pack(anchor = "n")
		Tab_RP_Canonicizers_Button.excludestyle = True

		self.Tab_RP_Canonicizers_Listbox = Listbox(Tab_ReviewProcess_Canonicizers)
		self.Tab_RP_Canonicizers_Listbox.pack(side = LEFT, expand = True, fill = BOTH)
		self.Tab_RP_Canonicizers_Listbox_scrollbar = Scrollbar(
			Tab_ReviewProcess_Canonicizers, width = self.dpi_setting["dpi_scrollbar_width"],
			command = self.Tab_RP_Canonicizers_Listbox.yview)
		self.Tab_RP_Canonicizers_Listbox_scrollbar.pack(side = RIGHT, fill = BOTH)
		self.Tab_RP_Canonicizers_Listbox.config(yscrollcommand = self.Tab_RP_Canonicizers_Listbox_scrollbar.set)

		Tab_RP_EventDrivers_Button = Button(
			Tab_ReviewProcess_EventDrivers,  text = "Event Drivers",font = ("helvetica", 16), relief = FLAT,
			command = lambda:self.switch_tabs(tabs, "choose", 2))
		Tab_RP_EventDrivers_Button.pack(anchor = "n")
		Tab_RP_EventDrivers_Button.excludestyle = True

		self.Tab_RP_EventDrivers_Listbox = Listbox(Tab_ReviewProcess_EventDrivers)
		self.Tab_RP_EventDrivers_Listbox.pack(side = LEFT, expand = True, fill = BOTH)
		self.Tab_RP_EventDrivers_Listbox_scrollbar = Scrollbar(
			Tab_ReviewProcess_EventDrivers,  width = self.dpi_setting["dpi_scrollbar_width"], 
			command = self.Tab_RP_EventDrivers_Listbox.yview)
		self.Tab_RP_EventDrivers_Listbox_scrollbar.pack(side = RIGHT, fill = BOTH)
		self.Tab_RP_EventDrivers_Listbox.config(yscrollcommand = self.Tab_RP_EventDrivers_Listbox_scrollbar.set)
		Tab_RP_EventCulling_Button = Button(
			Tab_ReviewProcess_EventCulling, text = "Event Culling",font = ("helvetica", 16), relief = FLAT,
			command = lambda:self.switch_tabs(tabs, "choose", 3))
		Tab_RP_EventCulling_Button.pack(anchor = "n")
		Tab_RP_EventCulling_Button.excludestyle = True

		self.Tab_RP_EventCulling_Listbox = Listbox(Tab_ReviewProcess_EventCulling)
		self.Tab_RP_EventCulling_Listbox.pack(side = LEFT, expand = True, fill = BOTH)
		self.Tab_RP_EventCulling_Listbox_scrollbar = Scrollbar(
			Tab_ReviewProcess_EventCulling, width = self.dpi_setting["dpi_scrollbar_width"],
			command = self.Tab_RP_EventCulling_Listbox.yview)
		self.Tab_RP_EventCulling_Listbox_scrollbar.pack(side = RIGHT, fill = BOTH)
		self.Tab_RP_EventCulling_Listbox.config(yscrollcommand = self.Tab_RP_EventCulling_Listbox_scrollbar.set)

		Tab_RP_Embeddings_Button = Button(
			Tab_ReviewProcess_Embeddings, text = "Embedders",font = ("helvetica", 16), relief = FLAT,
			command = lambda:self.switch_tabs(tabs, "choose", 4))
		Tab_RP_Embeddings_Button.pack(anchor = "n")
		Tab_RP_Embeddings_Button.excludestyle = True

		self.Tab_RP_Embeddings_Listbox = Listbox(Tab_ReviewProcess_Embeddings)
		self.Tab_RP_Embeddings_Listbox.pack(side = LEFT, expand = True, fill = BOTH)
		self.Tab_RP_Embeddings_Listbox_scrollbar = Scrollbar(
			Tab_ReviewProcess_Embeddings, width = self.dpi_setting["dpi_scrollbar_width"],
			command = self.Tab_RP_Embeddings_Listbox.yview)
		self.Tab_RP_Embeddings_Listbox_scrollbar.pack(side = RIGHT, fill = BOTH)
		self.Tab_RP_Embeddings_Listbox.config(yscrollcommand = self.Tab_RP_Embeddings_Listbox_scrollbar.set)

		Tab_RP_AnalysisMethods_Button = Button(
			Tab_ReviewProcess_AnalysisMethods, text = "Analysis Methods",font = ("helvetica", 16), relief = FLAT,
			command = lambda:self.switch_tabs(tabs, "choose", 5))
		Tab_RP_AnalysisMethods_Button.pack(anchor = "n")
		Tab_RP_AnalysisMethods_Button.excludestyle = True

		self.Tab_RP_AnalysisMethods_Listbox = ttk.Treeview(Tab_ReviewProcess_AnalysisMethods, columns = ("AM", "DF"))
		self.Tab_RP_AnalysisMethods_Listbox.column("#0", width = 0, stretch = NO)
		self.Tab_RP_AnalysisMethods_Listbox.heading("AM", text = "Method", anchor = W)
		self.Tab_RP_AnalysisMethods_Listbox.heading("DF", text = "Distance", anchor = W)

		self.Tab_RP_AnalysisMethods_Listbox.pack(side = LEFT, expand = True, fill = BOTH)
		self.Tab_RP_AnalysisMethods_Listbox_scrollbar = Scrollbar(
			Tab_ReviewProcess_AnalysisMethods,
			width = self.dpi_setting["dpi_scrollbar_width"],
			command = self.Tab_RP_AnalysisMethods_Listbox.yview)
		self.Tab_RP_AnalysisMethods_Listbox_scrollbar.pack(side = RIGHT, fill = BOTH)
		self.Tab_RP_AnalysisMethods_Listbox.config(yscrollcommand = self.Tab_RP_AnalysisMethods_Listbox_scrollbar.set)

		self.Tab_RP_ShowResults_Button = Button(
			self.tabs_frames["Tab_ReviewProcess"], text = "Show Results", width = 25,
			command=self.show_results_window
		)
		self.Tab_RP_ShowResults_Button.grid(row = 2, column = 0, columnspan = 3, sticky = "se", pady = 0, padx = 20)

		self.Tab_RP_Process_Button = Button(self.tabs_frames["Tab_ReviewProcess"], text = "Process", width = 25)
		# button command see after documents tab.
		self.Tab_RP_Process_Button.grid(row = 3, column = 0, columnspan = 3, sticky = "se", pady = (3, 5), padx = 20)

		self.Tab_RP_Process_Button.bind("<Map>",
			lambda event, a = [], lb = [self.Tab_RP_EventDrivers_Listbox, self.Tab_RP_Embeddings_Listbox, self.Tab_RP_AnalysisMethods_Listbox],
			labels = [Tab_RP_EventDrivers_Button, Tab_RP_Embeddings_Button, Tab_RP_AnalysisMethods_Button]:
			self.process_check(lb, labels)
		)
		
		self.Tab_RP_Process_Button.config(\
			command = lambda:self.run_experiment())


	def _documents_tab(self):

		Tab_Documents_topframe = Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_topframe.grid(row = 0, column = 0, sticky = 'EW', pady = (10, 5))

		Tab_Documents_Language_label = Label(
			Tab_Documents_topframe ,text = "Document Language", font = ("helvetica", 15), anchor = 'nw'
		)
		Tab_Documents_Language_label.grid(row = 0, column = 0, sticky = 'NW', pady = 0)

		# Tab_Documents_search_all = ttk.Combobox(Tab_Documents_topframe, width=30)
		# Tab_Documents_search_all.grid(row = 1, column = 1, sticky = "E", pady = 0)

		for n in range(10):
			if n == 5 or n == 8:
				w = 1
				self.tabs_frames["Tab_Documents"].columnconfigure(0, weight = 1)

			else: w = 0
			self.tabs_frames["Tab_Documents"].rowconfigure(n, weight = w)


		# !!! to allow for per-document language settings,
		# also change the spacy (canonicizer) module's langauge module loading functions.
		#documents-language selection
		analysisLanguage = StringVar()
		analysisLanguage.set(self.backend_API.languages_available[self.backend_API.default_language])
		#may need a lookup function for the options below
		analysisLanguageOptions = self.backend_API.languages_available
		Tab_Documents_language_dropdown = OptionMenu(
			Tab_Documents_topframe, analysisLanguage, *analysisLanguageOptions
		)
		Tab_Documents_language_dropdown.config(width = self.dpi_setting["dpi_language_dropdown_width"])
		Tab_Documents_language_dropdown['anchor'] = 'nw'
		Tab_Documents_language_dropdown.grid(row = 1, column = 0, sticky = 'NW')


		analysisLanguage.trace_add("write",
							lambda v1, v2, v3, p = "language", stringvar = analysisLanguage:
							self.set_API_global_parameters(p, stringvar))


		#documents-unknown authors
		Tab_Documents_UnknownAuthors_label =\
			Label(self.tabs_frames["Tab_Documents"], text = "Documents of unknown authors", font = ("helvetica", 15), anchor = 'nw')
		Tab_Documents_UnknownAuthors_label.grid(row = 4, column = 0, sticky = "W", pady = (10, 5))


		Tab_Documents_UnknownAuthors_Frame =\
			Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_UnknownAuthors_Frame.grid(row = 5, column = 0, sticky = "wnse")


		self.Tab_Documents_UnknownAuthors_listbox =\
			Listbox(Tab_Documents_UnknownAuthors_Frame, width = "100",
			#selectmode="multiple"
			)
		Tab_Documents_UnknownAuthors_listscrollbar =\
			Scrollbar(Tab_Documents_UnknownAuthors_Frame, width = self.dpi_setting["dpi_scrollbar_width"])
		#loop below: to be removed

		self.Tab_Documents_UnknownAuthors_listbox.config(
			yscrollcommand = Tab_Documents_UnknownAuthors_listscrollbar.set
		)
		Tab_Documents_UnknownAuthors_listscrollbar.config(
			command = self.Tab_Documents_UnknownAuthors_listbox.yview
		)


		self.Tab_Documents_UnknownAuthors_listbox.pack(side = LEFT, fill = BOTH, expand = True)
		Tab_Documents_UnknownAuthors_listscrollbar.pack(side = RIGHT, fill = BOTH, padx = (0, 30))

		Tab_Documents_doc_buttons = Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_doc_buttons.grid(row = 6, column = 0, sticky = "W")
		Tab_Documents_UnknownAuthors_AddDoc_Button = Button(
				Tab_Documents_doc_buttons, text = "Add Document", width = "16",
				command = lambda: self._edit_unknown_docs("add")
		)
		Tab_Documents_UnknownAuthors_RmvDoc_Button = Button(
			Tab_Documents_doc_buttons, text="Remove Document", width = "16",
			command=lambda: self._edit_unknown_docs("remove")
		)
		Tab_Documents_UnknownAuthors_clear_Button = Button(
			Tab_Documents_doc_buttons, text="CLEAR DOCUMENTS", width = "16",
			command=lambda: self._edit_unknown_docs("clear")
		)

		self.Tab_Documents_UnknownAuthors_doc_stats = Label(
			Tab_Documents_doc_buttons, text="Documents: 0", anchor="e", justify="right"
		)

		Tab_Documents_UnknownAuthors_AddDoc_Button.grid(row = 1, column = 1, sticky = "W")
		Tab_Documents_UnknownAuthors_RmvDoc_Button.grid(row = 1, column = 2, sticky = "W")
		Tab_Documents_UnknownAuthors_clear_Button.grid(row = 1, column = 3, sticky = "W")
		self.Tab_Documents_UnknownAuthors_doc_stats.grid(row = 1, column=4, sticky = "E", padx=(20, 0))

		#documents-known authors
		Tab_Documents_KnownAuthors_label = Label(
			self.tabs_frames["Tab_Documents"], text = "Known Authors", font = ("helvetica", 15), anchor = 'nw'
		)
		Tab_Documents_KnownAuthors_label.grid(row = 7, column = 0, sticky = "W", pady = (10, 5))


		Tab_Documents_KnownAuthors_Frame = Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_KnownAuthors_Frame.grid(row = 8, column = 0, sticky = "wnse")


		#self.Tab_Documents_KnownAuthors_treeview = Listbox(Tab_Documents_KnownAuthors_Frame, width = "100")
		self.Tab_Documents_KnownAuthors_treeview = ttk.Treeview(Tab_Documents_KnownAuthors_Frame, show="tree")
		Tab_Documents_KnownAuthors_listscroller = Scrollbar(Tab_Documents_KnownAuthors_Frame, width = self.dpi_setting["dpi_scrollbar_width"])

		self.Tab_Documents_KnownAuthors_treeview.config(
			yscrollcommand = Tab_Documents_KnownAuthors_listscroller.set
		)
		Tab_Documents_KnownAuthors_listscroller.config(command = self.Tab_Documents_KnownAuthors_treeview.yview)


		self.Tab_Documents_KnownAuthors_treeview.pack(side = LEFT, fill = BOTH, expand = True)
		Tab_Documents_KnownAuthors_listscroller.pack(side = RIGHT, fill = BOTH, padx = (0, 30))

		#These are known authors
		Tab_Documents_knownauth_buttons = Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_knownauth_buttons.grid(row = 9, column = 0, sticky = "W")
		Tab_Documents_KnownAuthors_AddAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Add Author", width = "15",
			command = lambda:self.edit_known_authors('add'))
		Tab_Documents_KnownAuthors_EditAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Edit Author", width = "15",
			command = lambda:self.edit_known_authors('edit'))
		Tab_Documents_KnownAuthors_RmvAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Remove Author", width = "15",
			command = lambda:self.edit_known_authors("remove"))
		Tab_Documents_KnownAuthors_ClrAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "CLEAR ALL", width = "15",
			command = lambda:self.edit_known_authors("clear"))
		self.Tab_Documents_KnownAuthors_doc_stats = Label(
			Tab_Documents_knownauth_buttons, text="Authors: 0 Docs: 0", anchor="e", justify="right"
		)

		Tab_Documents_KnownAuthors_AddAuth_Button.grid(row=1, column=1, sticky="W")
		Tab_Documents_KnownAuthors_EditAuth_Button.grid(row=1, column=2, sticky="W")
		Tab_Documents_KnownAuthors_RmvAuth_Button.grid(row=1, column=3, sticky="W")
		Tab_Documents_KnownAuthors_ClrAuth_Button.grid(row=1, column=4, sticky="W")
		self.Tab_Documents_KnownAuthors_doc_stats.grid(row=1, column=5, sticky="E", padx=(20, 0))

	def _unified_tabs(self):
		"""
		This is different from backend.GUI.GUI_unified_tabs.
		This calls the GUI_unified_tabs with parameters for each tab and saves the widget objects
		in self.generated_widgets.
		"""
		self.generated_widgets = dict()

		CanonicizerFormat = StringVar()
		# TODO move implementation of canonicizer file format to the API
		self.Tab_Canonicizers_parameters_displayed = []
		self.generated_widgets['Canonicizers'] = GUI_unified_tabs.create_module_tab(
			self.tabs_frames["Tab_Canonicizers"],
			["Canonicizers"],
			"Canonicizers",
			displayed_parameters = self.Tab_Canonicizers_parameters_displayed,
			canonicizers_format = CanonicizerFormat,
			RP_listbox = self.Tab_RP_Canonicizers_Listbox,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)
		Hovertip(self.generated_widgets["Canonicizers"]["available_listboxes"][0][1],
			self.tooltips.get("mod_type", dict()).get("Canonicizers", "Canonicize/normalize texts"))

		self.Tab_EventDrivers_parameters_displayed = []
		self.generated_widgets['EventDrivers'] = GUI_unified_tabs.create_module_tab(
			self.tabs_frames["Tab_EventDrivers"],
			["Event Drivers"],
			"EventDrivers",
			displayed_parameters = self.Tab_EventDrivers_parameters_displayed,
			RP_listbox = self.Tab_RP_EventDrivers_Listbox,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)
		Hovertip(self.generated_widgets["EventDrivers"]["available_listboxes"][0][1],
			self.tooltips.get("mod_type", dict()).get("EventDrivers", "Extract characteristic features/events"))

		self.Tab_EventCulling_parameters_displayed = []
		self.generated_widgets['EventCulling'] = GUI_unified_tabs.create_module_tab(
			self.tabs_frames["Tab_EventCulling"],
			["Feature & Event filtering"],
			"EventCulling",
			displayed_parameters = self.Tab_EventCulling_parameters_displayed,
			RP_listbox = self.Tab_RP_EventCulling_Listbox,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)
		Hovertip(self.generated_widgets["EventCulling"]["available_listboxes"][0][1],
			self.tooltips.get("mod_type", dict()).get("EventCulling", "Filter/discard irrelevant features/events"))

		self.Tab_Embeddings_parameters_displayed = []
		self.generated_widgets['Embeddings'] = GUI_unified_tabs.create_module_tab(
			self.tabs_frames["Tab_Embeddings"],
			["Embedding"],
			"Embeddings",
			displayed_parameters = self.Tab_Embeddings_parameters_displayed,
			RP_listbox = self.Tab_RP_Embeddings_Listbox,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)
		Hovertip(self.generated_widgets["Embeddings"]["available_listboxes"][0][1],
			self.tooltips.get("mod_type", dict()).get("Embeddings", "Convert text features to numbers for analysis"))

		self.Tab_AnalysisMethods_parameters_displayed = []
		self.generated_widgets['AnalysisMethods'] = GUI_unified_tabs.create_module_tab(
			self.tabs_frames["Tab_AnalysisMethods"],
			["Analysis Methods",
			"Distance Functions"],
			"AnalysisMethods",
			RP_listbox = self.Tab_RP_AnalysisMethods_Listbox,
			displayed_parameters = self.Tab_AnalysisMethods_parameters_displayed,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)
		Hovertip(self.generated_widgets["AnalysisMethods"]["available_listboxes"][0][1],
			self.tooltips.get("mod_type", dict()).get("AnalysisMethods", "Use statistics/machine learning to classify documents"))
		Hovertip(self.generated_widgets["AnalysisMethods"]["available_listboxes"][1][1],
			self.tooltips.get("mod_type", dict()).get("DistanceFunctions", "Specify a distance metric, if applicable"))


		for mtype in ['Canonicizers', "EventDrivers", "EventCulling", "Embeddings", "AnalysisMethods"]:
			self.search_entry_query[mtype] = StringVar()
			self.generated_widgets[mtype]['search_entry']\
				.configure(textvariable=self.search_entry_query[mtype])
			self.generated_widgets[mtype]['search_entry'].bind('<Control-A>',
				lambda event: self.generated_widgets[mtype]['search_entry'].select_range(0, END))
			self.search_entry_query[mtype].trace_add(
				"write", callback=lambda v1, v2, v3,
				entry=self.generated_widgets[mtype]['search_entry'],
				lb=self.generated_widgets[mtype]["available_listboxes"][0][2],
				search_from=list(self.backend_API.moduleTypeDict[mtype].keys()):\
				self.search_modules(entry, lb, search_from)
			)

		self.search_entry_query["DistanceFunctions"] = StringVar()
		self.generated_widgets["AnalysisMethods"]['search_entry']\
			.configure(textvariable=self.search_entry_query["AnalysisMethods"])
		self.generated_widgets["AnalysisMethods"]['search_entry'].bind('<Control-A>',
			lambda event: self.generated_widgets["AnalysisMethods"]['search_entry'].select_range(0, END))
		self.search_entry_query["AnalysisMethods"].trace_add(
			"write", callback=lambda v1, v2, v3,
			entry=self.generated_widgets["AnalysisMethods"]['search_entry'],
			lb=self.generated_widgets["AnalysisMethods"]["available_listboxes"][1][2],
			search_from=list(self.backend_API.moduleTypeDict["DistanceFunctions"].keys()):\
			self.search_modules(entry, lb, search_from)
		)

	#ABOVE ARE THE CONFIGS FOR EACH TAB
	def _bottom_frame(self):

		bottomframe = Frame(self.topwindow, height = 150, width = 570)
		bottomframe.columnconfigure(0, weight = 1)
		bottomframe.rowconfigure(1, weight = 1)
		bottomframe.grid(pady = 10, row = 1, sticky = 'swen')

		for c in range(6):
			bottomframe.columnconfigure(c, weight = 10)

		finish_button = Button(bottomframe, text = "Finish & Review", command = lambda:self.switch_tabs(self.tabs, "choose", 6))
		#note: this button has a hard-coded tab number
		previous_button = Button(bottomframe, text = "<< Previous", command = lambda:self.switch_tabs(self.tabs, "previous"))
		next_button = Button(bottomframe, text = "Next >>", command = lambda:self.switch_tabs(self.tabs, "next"))
		notes_button = Button(bottomframe, text = "Notes", command = self.notepad)

		Label(bottomframe).grid(row = 0, column = 0)
		Label(bottomframe).grid(row = 0, column = 5)

		previous_button.grid(row = 0, column = 1, sticky = 'swen')
		next_button.grid(row = 0, column = 2, sticky = 'swen')
		notes_button.grid(row = 0, column = 3, sticky = 'swen')
		finish_button.grid(row = 0, column = 4, sticky = 'swen')

		statusbar = Frame(self.topwindow, bd = 1, relief = SUNKEN)
		statusbar.grid(row = 2, sticky = "swe")

		welcome_message = "By David Berdik and Michael Fang. Version date: %s." %(Constants.versiondate)
		self.statusbar_label = Label(statusbar, text = welcome_message, anchor = W)
		self.statusbar_label.pack(anchor = "e")
		self.topwindow.after(3000, lambda:self.status_update("", welcome_message))

	def displayAbout(self):
		"""Displays the About Page"""
		if GUI_debug >= 3: print("displayAbout()")
		try:
			self.about_page.lift()
			return
		except (NameError, AttributeError, TclError):
			pass
		self.about_page = Toplevel()
		self.about_page.title("About PyGAAP")
		self.about_page.geometry(self.dpi_setting["dpi_about_page_geometry"])
		self.about_page.resizable(False, False)
		about_page_logosource = PhotoImage(file = "./res/logo.png")
		about_page_logosource = about_page_logosource.subsample(2, 2)
		AboutPage_logo = Label(self.about_page, image = about_page_logosource)
		AboutPage_logo.pack(side = "top", fill = "both", expand = "yes")

		textinfo = ("THIS IS AN EARLY VERSION OF PyGAAP GUI.\n"
		+ "Version date: " + str(Constants.versiondate)
		+ "\nPyGAAP is a Python port of JGAAP,\n"
		+ "Java Graphical Authorship Attribution Program.\n"
		+ "This is an open-source tool developed by the EVL Lab\n"
		+ "(Evaluating Variation in Language Laboratory).")
		AboutPage_text = Label(self.about_page, text = textinfo)
		AboutPage_text.pack(side = 'bottom', fill = 'both', expand = 'yes')
		self.about_page.mainloop()

	def file_add_remove(self, window_title, listbox_operate: Listbox, allow_duplicates: bool, function: str, lift_window = None):
		"""Universal add file function to bring up the explorer window"""
		# window_title is the title of the window,
		# may change depending on what kind of files are added
		# listbox_operate is the listbox object to operate on
		# allow_duplicates is whether the listbox allows duplicates.
		# if listbox does not allow duplicates,
		# item won't be added to the listbox and this prints a message to the terminal.
		# lift_window is the window to go back to focus when the file browser closes
		if GUI_debug >= 1: print("self.file_add_remove")
		elif GUI_debug >= 3: print("self.file_add_remove(allow_duplicates = %s)", allow_duplicates)
		if function == "add":
			filename = askopenfilename(
				filetypes = (("Text File", "*.txt"), ("All Files", "*.*")),
				title = window_title, multiple = True
			)
			if lift_window != None:
				lift_window.lift(self.topwindow)
			if allow_duplicates and filename != "" and len(filename) > 0:
				listbox_operate.insert(END, filename)
			else:
				for fileinlist in listbox_operate.get(0, END):
					if fileinlist == filename:
						self.status_update("File already in list.")
						if GUI_debug > 0:
							print("Add document: file already in list")
						lift_window.lift()
						return
				if filename != None and filename != "" and len(filename) > 0:
					for file in filename:
						listbox_operate.insert(END, file)

			if lift_window != None:
				lift_window.lift()
			return
		elif function == "remove":
			try:
				listbox_operate.delete(listbox_operate.curselection())
				self.status_update()
			except TclError:
				self.status_update("Nothing selected")
				return


	def _docs_to_string_list(self):
		# return {
		# 	"unknown": [str(doc.filepath) for doc in self.backend_API.unknown_docs],
		# 	"known": [str(doc.filepath) for doc in self.backend_API.known_authors]
		# }
		return {
			"unknown": [str(doc.filepath) for doc in self.backend_API.unknown_docs],
			"known": [doc for auth in self.backend_API.known_authors for doc in auth]
		}

	def _edit_unknown_docs(self, mode, **options):
		"""Edit list of unknown docs"""
		# modes: "add", "remove", or "clear"
		if GUI_debug >= 3: print("_edit_unknown_docs(mode=%s)"%(mode))
		if mode == "clear":
			self.backend_API.unknown_docs = []
			self.Tab_Documents_UnknownAuthors_listbox.delete(0, END)
		elif mode == "remove":
			selected = self.Tab_Documents_UnknownAuthors_listbox.curselection()
			if len(selected) == 0:
				self.status_update("Nothing selected")
				return
			else:
				# first find what the new list looks like
				self.backend_API.unknown_docs = \
					[self.backend_API.unknown_docs[x] for \
						x in range(len(self.backend_API.unknown_docs))
						if x not in selected]
				# refresh listbox by clearing and then adding from backend_API's doc list.
				self.Tab_Documents_UnknownAuthors_listbox.delete(0, END)
				for item in self._docs_to_string_list()["unknown"]:
					self.Tab_Documents_UnknownAuthors_listbox.insert(END, item)
			# automatically select closest item after previous is deleted
			# good for quick-fire chain deletion.
			if len(self.backend_API.unknown_docs) > 0:
				after_choose = selected[0]
				if selected[0] == len(self.backend_API.unknown_docs):
					after_choose -= 1
				self.Tab_Documents_UnknownAuthors_listbox.select_set(max(after_choose, 0))
		elif mode == "add":
			if not options.get("test", False):
				add_list = askopenfilename(
					filetypes=(("Text File", "*.txt"), ("All Files", "*.*")),
					title="Add Unknown Document(s)", multiple=True
				)
			else: add_list = options.get("add_list")
			if type(add_list) == str: add_list = (add_list,)
			for item in add_list:
				# do not read documents and save content to Document.text. Read only when processing.
				self.backend_API.unknown_docs.append(Document("", item.split("/")[-1], "", item))
				self.Tab_Documents_UnknownAuthors_listbox.insert(END, item)

		elif "autoadd" in mode:
			if "clear" in mode: self._edit_unknown_docs("clear")
			add_list = options.get("add_list")
			for item in add_list:
				self.backend_API.unknown_docs.append(item)
			for item in self._docs_to_string_list()["unknown"]:
				self.Tab_Documents_UnknownAuthors_listbox.insert(END, item)
		self.Tab_Documents_UnknownAuthors_doc_stats["text"] = "Documents: " + str(len(self.backend_API.unknown_docs))


	def _load_modules_to_GUI(self, startup=False):

		# first clear everthing in listboxes.
		# the "DistanceFunctions" Treeview is in the "AnalysisMethods" tkinter frame.
		for module_type in ["Canonicizers", "EventDrivers", "EventCulling", "Embeddings"]:
			self.generated_widgets[module_type]["available_listboxes"][0][2].delete(0, END)
			self.generated_widgets[module_type]["selected_listboxes"][0][2].delete(0, END)
		for listbox in [self.Tab_RP_Canonicizers_Listbox,
						self.Tab_RP_EventDrivers_Listbox,
						self.Tab_RP_EventCulling_Listbox,
						self.Tab_RP_Embeddings_Listbox]:
			listbox.delete(0, END)

		self.Tab_RP_AnalysisMethods_Listbox.delete(*self.Tab_RP_AnalysisMethods_Listbox.get_children())
		self.generated_widgets["AnalysisMethods"]["available_listboxes"][1][2].delete(0, END)
		self.generated_widgets["AnalysisMethods"]["available_listboxes"][0][2].delete(0, END)
		amdf = self.generated_widgets["AnalysisMethods"]["selected_listboxes"][0][2]
		amdf.delete(*amdf.get_children())

		try:
			# adding items to listboxes from the backend_API.
			for canonicizer in sorted(list(self.backend_API.canonicizers.keys())):
				self.generated_widgets["Canonicizers"]["available_listboxes"][0][2].insert(END, canonicizer)
			for driver in sorted(list(self.backend_API.eventDrivers.keys())):
				self.generated_widgets["EventDrivers"]["available_listboxes"][0][2].insert(END, driver)
			for distancefunc in sorted(list(self.backend_API.distanceFunctions.keys())):
				assert distancefunc != "NA", 'Distance Function cannot have the name "NA" ' \
				+ '(Reserved for Analysis methods that do not use a distance function).\n' \
				+ 'Please check the file containing the definition of the distance function class, ' \
				+ 'most likely in or imported to DistanceFunction.py,\nand change the return of displayName().'
				self.generated_widgets["AnalysisMethods"]["available_listboxes"][1][2].insert(END, distancefunc)
			for culling in sorted(list(self.backend_API.eventCulling.keys())):
				self.generated_widgets["EventCulling"]["available_listboxes"][0][2].insert(END, culling)
			for converter in sorted(list(self.backend_API.embeddings.keys())):
				self.generated_widgets["Embeddings"]["available_listboxes"][0][2].insert(END, converter)
			for method in sorted(list(self.backend_API.analysisMethods.keys())):
				self.generated_widgets["AnalysisMethods"]["available_listboxes"][0][2].insert(END, method)
			if startup == False: self.status_update("Modules reloaded")
			return
		except Exception as e:
			error_window = Toplevel()
			error_window.geometry(self.dpi_setting["dpi_process_window_geometry_finished"])
			error_window.title("Error while loading modules")
			error_text_field = Text(error_window)
			error_text_field.pack(fill=BOTH, expand=True)
			
			error_text = "An error occurred while loading the modules:\n\n"
			error_text += str(exc_info()[0]) + "\n" + str(exc_info()[1]) + "\n" + str(exc_info()[2].tb_frame.f_code)
			error_text += '\n\nDevelopers: Reload modules by going to "developers" -> "Reload modules"'
			error_text_field.insert(END, error_text)
			topwindow.after(1200, error_window.lift)
			if startup == False: self.status_update("Error while loading modules, see pop-up window.")
			#exc_type, exc_obj, exc_tb = exc_info()
			return
		#######

	def expanded_search(self, query, mod_name, mode="forwards"):
		"""
		This expands search terms to itself along with common substitutions.
		e.g. it expands "neural network" to "neural network" and "perceptron".
		Inspired by Cinnamon's (DE) search function that shows "LibreOffice calc"
		when queried with "excel".
		Forwards and backwards search: see comments in ./backend/GUI/search_dictinoary.json
		forwards is consistent with JGAAP.
		"""
		mod_name = mod_name.replace("-", " ")
		query = query.replace("-", " ")
		if query in mod_name: return True
		# query is not empty below this line (mod_name is never empty)
		if query in "".join([x[0] for x in mod_name.split()]): return True
		if mode == "backwards":
			search = self.search_dictionary["backwards"]
			expanded_terms = [mod_name]
			for key in search:
				if key in mod_name:
					for alt_term in search[key]:
						if query in alt_term: return True
			return False
		if mode == "forwards":
			search = self.search_dictionary["forwards"]
			expanded_terms = [query]
			for key in search:
				if query in key:
					# no need to check if key in mod_name
					# because from above: query not in mod_name,
					# and query in key, therefore key not in mod_name.
					for alt_term in search[key]:
						if alt_term in mod_name: return True
			return False

	def search_modules(self, search_entry, listbox, search_from):
		"""
		Alter what's displayed in the listbox from search query.
		If entry is empty, display all as usual.
		"""
		query = search_entry.get().lower().strip() # string
		retrieve = {x.strip().lower():x for x in search_from}
		candidates = [retrieve[item] for item in list(retrieve.keys()) if
			self.expanded_search(query, item)]
		candidates.sort()
		listbox.delete(0, END)
		for c in candidates:
			listbox.insert(END, c)
		return

	
	def select_modules(self, listbox_available: Listbox,
					Listbox_operate: list,
					function: str,
					**options):
		"""Used by Event Drivers, Event culling etc to
		add/remove/clear selected modules.
		Needs to check if module is already added."""

		# listbox_available: listbox with available modules
		# Listbox_operate: a list of listboxes to modify.
		#   Includes the one in the corresponding tab and the
		#   listbox in the Review & Process tab.
		# function: "clear", "remove", or "add"

		if function == "clear":
			if GUI_debug > 1: print("select_modules: clear")
			for listbox_member in Listbox_operate:
				if type(listbox_member) == Listbox:
					listbox_member.delete(0, END)
				else:
					listbox_member.delete(*listbox_member.get_children())
			module_type = options.get("module_type")
			self.backend_API.modulesInUse[module_type].clear()
			if module_type == "AnalysisMethods":
				self.backend_API.modulesInUse["DistanceFunctions"].clear()
			return

		elif function == "remove":
			if GUI_debug > 1: print("select_modules: remove")
			module_type = options.get("module_type")
			try:
				if type(Listbox_operate[0]) == Listbox:
					removed = Listbox_operate[0].curselection()
					assert len(removed) > 0
				else:
					removed = Listbox_operate[0].selection()
					removed_index = Listbox_operate[0].index(removed)
				self.status_update()
				for listbox_member in Listbox_operate:
					listbox_member.delete(removed)
			
			except (ValueError, AssertionError, TclError):
				if GUI_debug > 0: print("remove from list: nothing selected or empty list.")
				self.status_update("Nothing selected.")
				return
			if type(Listbox_operate[0]) == Listbox:
					self.backend_API.modulesInUse[module_type].pop(removed[0])
			else:
				self.backend_API.modulesInUse[module_type].pop(removed_index)
				self.backend_API.modulesInUse["DistanceFunctions"].pop(removed_index)
			return

		elif function == "add":
			if GUI_debug > 1: print("select_modules: add")
			module_type = options.get("module_type")
			try:
				if type(Listbox_operate[0]) == Listbox:
					# canonicizers, event drivers, event cullers.
					selected_module =\
						listbox_available[0].get(listbox_available[0].curselection())
					self.backend_API.modulesInUse[module_type].append(
						self.backend_API.moduleTypeDict[module_type].get(selected_module)()
					)
				elif len(listbox_available) > 1 \
						and listbox_available[1]['state'] == DISABLED:
					# analysis methods, no distance function
					selected_module =\
						(listbox_available[0].get(listbox_available[0].curselection()), "NA")
					self.backend_API.modulesInUse[module_type].append(
						self.backend_API.moduleTypeDict[module_type].get(selected_module[0])()
					)
					self.backend_API.modulesInUse["DistanceFunctions"].append("NA")
				else:
					# analysis methods with distance function
					selected_module = [
						listbox_available[0].get(listbox_available[0].curselection()),
						listbox_available[1].get(listbox_available[1].curselection())
					]
					self.backend_API.modulesInUse["AnalysisMethods"].append(
						self.backend_API.moduleTypeDict[module_type].get(selected_module[0])()
					)
					self.backend_API.modulesInUse["DistanceFunctions"].append(
						self.backend_API.moduleTypeDict["DistanceFunctions"].get(selected_module[1])()
					)
				self.status_update()

			except TclError:
				self.status_update("Nothing selected or missing selection.")
				if GUI_debug > 0: print("add to list: nothing selected")
				return
			except Exception as e:
				self.show_error_window(
					"Something went wrong while adding the module.\n\n"
					+ format_exc()
				)
				return

			for listbox_member in Listbox_operate:
				if type(Listbox_operate[0]) == Listbox:
					listbox_member.insert(END, selected_module)
				else:
					listbox_member.insert(parent = "",
										index = END,
										text = "",
										value = selected_module)

		else:
			self.status_update("Bug: all escaped: 'select_modules(function = %s).'"%(function))
			raise ValueError("Bug: all escaped: 'select_modules(function = %s).'"%(function))
		return


	def check_DF_listbox(self, lbAv, lbOp: Listbox):
		"""Enable or disable the 'Distance Functions' listbox ...
		depending on whether the item selected in
		'Analysis Methods' allows using DFs."""
		if GUI_debug >= 3: print("check_DF_listbox()")
		try:
			if self.backend_API.analysisMethods[lbAv.get(lbAv.curselection())]\
					.__dict__.get("_NoDistanceFunction_", False):
				lbOp.config(state = DISABLED)
			else:
				lbOp.config(state = NORMAL)
		except TclError:
			return

	def find_parameters(self,
						param_frame: Frame,
						listbox: Listbox or ttk.Treeview,
						displayed_params: list,
						clear: bool = False,
					**options):

		"""find parameters and description in some modules to display and set"""

		# param_frame: the tkinter frame that displays the parameters.
		# listbox: the tkinter listbox that has the selected parameters.
		# displayed_params: a list of currently displayed parameter options.
		# clear: True if function only used to clear displayed parameters.
		if GUI_debug >= 3:
			print("find_parameters(clear = %s), displayed_params list length: %s."
			%(clear, len(displayed_params)))


		module_type = options.get("module_type")
		# get dict of modules in the selected UI page.
		# first get the parameters to display from list.
		if type(listbox) == Listbox and len(listbox.curselection()) > 0:
			# event drivers, event cullers
			module_index = listbox.curselection()[0]
			this_module = self.backend_API.modulesInUse[module_type][module_index]
			this_module_name = listbox.get(module_index)
		elif type(listbox) == ttk.Treeview and len(listbox.selection()) > 0:
			# analysis methods, distance functions
			module_index = listbox.index(listbox.selection())
			this_module = self.backend_API.modulesInUse[module_type][module_index]
			this_df_module = self.backend_API.modulesInUse["DistanceFunctions"][module_index]
			# if not string "NA", this gets the df object.
			this_module_name = listbox.item(listbox.selection())["values"][0]
			this_df_module_name = listbox.item(listbox.selection())["values"][1]
			# this is the way to retrieve treeview selection names
		else: return
		
		for params in displayed_params:
			params.destroy()
		displayed_params.clear()
		if clear == True:
			return
		
		
		param_options = []
		# list of StringVars.
		if type(listbox) == Listbox:
			n_params = sum([1 for k in this_module._variable_options
				if this_module._variable_options[k].get("show", True)])
		else:
			try:
				df_variables = this_df_module._variable_options
			except AttributeError:
				df_variables = []
			n_params = sum([1 for k in this_module._variable_options
				if this_module._variable_options[k].get("show", True)]) \
							+ len(df_variables)
			number_of_am = sum([1 for k in this_module._variable_options
				if this_module._variable_options[k].get("show", True)])
		if n_params == 0:
			# if this module does not have parameters to be set, say so.
			displayed_params.append(Label(param_frame,
									text = "No parameters for this module."))
			displayed_params[-1].pack()
			return
		# if this module has parameters, find and display parameters.
		rowshift = 0
		# this is the row shift for widgets below the second tkinter.Label.
		# It's non-zero for when there are two groups of parameters to display.
		# (Analysis + DF)
		displayed_params.append(Label(param_frame,
									text = str(this_module_name) + ":",
									font = ("Helvetica", 14)))
		displayed_params[-1].grid(row = 0, column = 0, columnspan = 2, sticky = W)
		for i in range(len(this_module._variable_options)):
			if type(listbox) == Listbox:
				parameter_i = list(this_module._variable_options.keys())[i]
				# skip hidden parameters. good for dynamic param changes
				if not this_module._variable_options.get(parameter_i, {}).get("show", True): continue
				param_options.append(StringVar(
					value = str(this_module.__dict__.get(parameter_i)))
				)
			elif type(listbox) == ttk.Treeview:
				if i < number_of_am:
					parameter_i = list(this_module._variable_options.keys())[i]
					if not this_module._variable_options.get(parameter_i, {}).get("show", True): continue
					param_options.append(StringVar(
					value = str(this_module.__dict__.get(parameter_i)))
				)
				else:
					rowshift = 1
					if this_df_module == "NA": break
					parameter_i = list(this_df_module._variable_options.keys())[i - number_of_am]
					if not this_df_module._variable_options.get(parameter_i, {}).get("show", True): continue
					param_options.append(StringVar(
					value = str(this_df_module._variable_options[parameter_i]["options"]\
						[this_df_module._variable_options[parameter_i]["default"]]))
				)
			displayed_param_name = this_module._variable_options[parameter_i].get("displayed_name", parameter_i)
			displayed_params.append(Label(param_frame, text = displayed_param_name))
			displayed_params[-1].grid(row = i + 1 + rowshift, column = 0)

			menu_type = this_module._variable_options[parameter_i].get("type", "OptionMenu")
			if menu_type == 'Entry':
				raise NotImplementedError
				# TODO 2 priority low:
				# implement text entry for parameters.
				displayed_params.append(Entry(param_frame))
				displayed_params[-1].insert(
					0, str(parameter_i['options'][parameter_i])
				)
				displayed_params[-1].grid(row = i + 1 + rowshift, column = 1, sticky = W)
			elif menu_type == "OptionMenu":
				displayed_params.append(
					OptionMenu(
						param_frame, 
						param_options[-1],
						*this_module._variable_options[parameter_i]['options']
					)
				)
				displayed_params[-1].config(width = self.dpi_setting["dpi_option_menu_width"])
				displayed_params[-1].grid(row = i + 1 + rowshift, column = 1, sticky = "EW")
				param_options[-1].trace_add(("write"),
					lambda v1, v2, v3, stringvar = param_options[-1],
					module = this_module, var = parameter_i:\
						self.set_parameters(stringvar, module, var,
						param_frame=param_frame, listbox=listbox, dp=displayed_params, module_type=module_type))
			elif menu_type in ["Slider", "Scale"]:
				scale_begin = this_module._variable_options[parameter_i]["options"][0]
				scale_end = this_module._variable_options[parameter_i]["options"][-1]
				displayed_params.append(
					Scale(param_frame,
						orient="horizontal", tickinterval=scale_end-scale_begin,
						from_=scale_begin, to=scale_end, length=200,
						resolution=this_module._variable_options[parameter_i].get("resolution", 1),
						command=lambda value, module=this_module, var=parameter_i: self.set_parameters(
							value, module, var,
							param_frame=param_frame, listbox=listbox, dp=displayed_params, module_type=module_type,
						)
					)
				)
				displayed_params[-1].set(this_module.__dict__.get(parameter_i))
				displayed_params[-1].grid(row = i + 1 + rowshift, column = 1, sticky = "EW")
			elif menu_type in ["Tick", "Check"]:
				displayed_params.append(
					Checkbutton(
						param_frame, variable=param_options[-1],
						command=lambda value=param_options[-1], module=this_module, var=parameter_i:
							self.set_parameters(value, module, var,
								param_frame=param_frame, listbox=listbox, dp=displayed_params, module_type=module_type	
							)
					)
				)
				displayed_params[-1].grid(row = i + 1 + rowshift, column = 1, sticky = W)
			else:
				raise ValueError("Unknown input widget type", menu_type)
		if rowshift == 1:
			# if the rows are shifted, there is an extra label for the DF parameters.
			displayed_params.append(Label(param_frame,
				text = str(this_df_module_name) + ":",
				font = ("Helvetica", 14)))
			displayed_params[-1].grid(
				row = number_of_am + 1,
				column = 0,
				columnspan = 2,
				sticky = W)


		param_frame.columnconfigure(0, weight = 1)
		param_frame.columnconfigure(1, weight = 3)
		return

	def find_description(self,
						desc: Text,
						listbox: Listbox or ttk.Treeview,
						API_dict: dict):

		"""find description of a module."""

		# desc: the tkinter Text object to display the description.
		# listbox: the Listbox or Treeview object to get the selection from
		# API_dict: the API dictionary that contains
		#   the listed method classes from the backend.
		#   example -- API_dict could be backend_API.canonicizers.

		if GUI_debug >= 3: print("find_description()")

		if type(listbox) == Listbox:
			try:
				name = listbox.get(listbox.curselection())
				description_string = name + ":\n" \
										+ API_dict[name].displayDescription()
			except (TypeError, TclError):
				description_string = "No description"

		elif type(listbox) == ttk.Treeview:
			if listbox.item(listbox.selection())["values"] == "":
				description_string = ""
			else:
				am_name = listbox.item(listbox.selection())["values"][0]
				df_name = listbox.item(listbox.selection())["values"][1]
				am_d, df_d = "No description", "No description"
				try: am_d = self.backend_API.analysisMethods[am_name].displayDescription()
				except (TypeError, KeyError): pass
				try: df_d = self.backend_API.analysisMethods[df_name].displayDescription()
				except (TypeError, KeyError): pass
				if df_name == "NA": df_d = "Not applicable"
				description_string = am_name + ":\n" + am_d + "\n\n" + df_name + ":\n" + df_d

		desc.config(state = NORMAL)
		desc.delete(1.0, END)
		desc.insert(END, description_string)
		desc.config(state = DISABLED)
		return

	def set_parameters(self, stringvar, module, variable_name, **options):
		# ctrl-f: change_params change params edit params
		"""sets parameters whenever the widget is touched."""
		# stringvar: the value to set the parameter
		if GUI_debug >= 3:
			print("set_parameters(module = %s, variable_name = %s)"
			%(module, variable_name))
		value_to = stringvar.get() if type(stringvar) == StringVar else stringvar
		if type(value_to) != bool:
			try: # to identify numbers
				value_to = float(value_to)
				# if value is a number, try converting to a number.
				if abs(int(value_to) - value_to) < 1e-63:
					value_to = int(value_to)
			except ValueError:
				pass
		#setattr(module, variable_name, value_to)
		set_param_return = module.set_attr(variable_name, value_to)
		if set_param_return:
			self.find_parameters(options.get("param_frame"), options.get("listbox"), options.get("dp"),
				module_type=options.get("module_type"))
		return

	def set_API_global_parameters(self, parameter, stringvar):
		"""Wrapper for backend_API's global parameter setter"""
		if GUI_debug > 3: print("set api global parameters: %s" % parameter)
		self.backend_API.set_global_parameters(parameter, stringvar.get())
		return

	def show_API_process_content(self):
		"""
		show list of modules in use.
		The API.show_process_content is called here to avoid keeping a pointer
		to the old API when reloading modules.
		"""
		self.backend_API.show_process_content()

	def gui(self):
		"""This arranges the elements of the GUI. Calls helpers for some tasks."""
		#create window
		topwindow = Tk()
		self.topwindow = topwindow
		topwindow.title(self.gui_params["topwindow_title"])

		# set icon
		try:topwindow.tk.call(
				'wm',
				'iconphoto',
				topwindow._w,
				PhotoImage(file = './res/icon.png'))
		except TclError:
			print("Error: icon.png not found.")

		# establish top-middle-bottom layout
		topwindow.rowconfigure(0, weight = 1)
		topwindow.rowconfigure(1, weight = 0, minsize = 50)
		topwindow.columnconfigure(0, weight = 1)

		# determine element sizes
		dpi = topwindow.winfo_fpixels('1i')
		dpi_setting = None

		if dpi > 72:
			if GUI_debug >= 2: print("1x UI scale")
			self.dpi_setting = self.gui_params["dpi"]["small"]
			topwindow.geometry(self.gui_params["dpi"]["small"]["dpi_top_window_geometry"])
			self.ttk_style = ttk.Style()
			self.ttk_style.configure('Treeview', rowheight = self.gui_params["dpi"]["small"]["Treeview.rowheight"])
		else:
			if GUI_debug >= 2: print("2x UI scale")
			self.dpi_setting = self.gui_params["dpi"]["large"]
			topwindow.geometry(self.gui_params["dpi"]["large"]["dpi_top_window_geometry"])
			self.ttk_style = ttk.Style()
			self.ttk_style.configure('Treeview', rowheight = self.gui_params["dpi"]["large"]["Treeview.rowheight"])
		self.ttk_style.map(
			'Treeview',
			background = [('selected', self.gui_params["styles"][self.style_choice]["accent_color_mid"])],
			foreground = [('selected', "#000000")]
		)

		menubar = Menu(topwindow)
		menu_file = Menu(menubar, tearoff = 0)

		self.Tab_Documents_UnknownAuthors_listbox = None
		self.Tab_Documents_KnownAuthors_treeview = None

		#tkinter menu building goes from bottom to top / leaves to root
		menu_batch_documents = Menu(menu_file, tearoff = 0)#batch documents menu
		menu_batch_documents.add_command(
			label = "Save corpus csv",
			command = lambda function = "save":
			self.load_save_csv(function)
		)
		menu_batch_documents.add_command(
			label="Load corpus csv",
			command=lambda function = "load":
				self.load_save_csv(function)
		)
		menu_batch_documents.add_command(
			label="Clear and load corpus csv",
			command=lambda function = "load_clear":
				self.load_save_csv(function)
		)
		menu_file.add_cascade(
			label = "Batch Documents", menu = menu_batch_documents,
			underline = 0
		)

		menu_AAAC_problems = Menu(menu_file, tearoff = 0)
		
		for l in "ABCDEFGHIJKLM":
			menu_AAAC_problems.add_command(label="Problem "+l, command=lambda p=l:self.load_aaac(l))

		menu_file.add_cascade(
			label = "AAAC Problems", menu = menu_AAAC_problems,
			underline = 0
		)

		menu_file.add_separator()#file menu
		menu_themes = Menu(menu_file, tearoff = 0)
		menu_themes.add_command(
			label = "PyGaap Pink", command = lambda thm = "PyGAAP_pink":self.change_style_live(thm)
		)
		menu_themes.add_command(
			label = "JGAAP Blue", command = lambda thm = "JGAAP_blue":self.change_style_live(thm)
		)
		menu_file.add_cascade(label = "Themes", menu = menu_themes, underline = 0)

		menu_file.add_separator()#file menu
		menu_file.add_command(label = "Exit", command = topwindow.destroy)
		menubar.add_cascade(label = "File", menu = menu_file)

		menu_help = Menu(menubar, tearoff = 0) #help menu
		menu_help.add_command(label = "About...", command = self.displayAbout)
		menubar.add_cascade(label = "Help", menu = menu_help)

		menu_dev = Menu(menubar, tearoff=0)
		#menu_dev.add_command(label="Instant experiment", command=self.instant_experiment)
		menu_dev.add_command(label="Reload modules", command=self.reload_modules)
		menu_dev.add_command(label="Show process content", command=self.show_API_process_content)
		menu_dev.add_command(label="Toggle built-in multiprocessing", command=self.toggle_mp)
		menubar.add_cascade(label="Developer", menu=menu_dev)

		topwindow.config(menu = menubar)
		#bottom of the main window is at the bottom of this file


		#the middle workspace where the tabs are

		workspace = Frame(topwindow, height = 800, width = 570)
		workspace.grid(padx = 10, pady = 5, row = 0, sticky = "nswe")
		workspace.columnconfigure(0, weight = 1)
		workspace.rowconfigure(0, weight = 2)

		self.tabs = ttk.Notebook(workspace)
		self.tabs.enable_traversal()
		self.tabs.pack(pady = 1, padx = 5, expand = True, fill = "both")

		# add tabs
		for t in self.tabs_names:
			self.tabs_frames[t] = Frame(self.tabs, height = self.gui_params["tabheight"], width = self.gui_params["tabwidth"])
			self.tabs_frames[t].pack(fill = 'both', expand = True, anchor = NW)


		self.tabs.add(self.tabs_frames["Tab_Documents"], text = "Data")
		self.tabs.add(self.tabs_frames["Tab_Canonicizers"], text = "Normalization")
		self.tabs.add(self.tabs_frames["Tab_EventDrivers"], text = "Feature Extraction")
		self.tabs.add(self.tabs_frames["Tab_EventCulling"], text = "Feature Filtering")
		self.tabs.add(self.tabs_frames["Tab_Embeddings"], text = "Embedding")
		self.tabs.add(self.tabs_frames["Tab_AnalysisMethods"], text = "Analysis Methods")
		self.tabs.add(self.tabs_frames["Tab_ReviewProcess"], text = "Review & Process")

		# add various tabs
		self._review_process_tab(self.tabs)
		self._documents_tab()
		self._unified_tabs()

		self._load_modules_to_GUI(True)
		self._bottom_frame()
		self.change_style(self.topwindow)

	def change_style(self, parent_widget):
		"""This changes the colors of the widgets."""
		if GUI_debug >= 4: print("change_style(parent_widget = %s)"%(parent_widget))
		if len(parent_widget.winfo_children()) == 0: return
		for widget in parent_widget.winfo_children():
			if isinstance(widget, Button) and "excludestyle" not in widget.__dict__:
				widget.configure(
					activebackground = self.gui_params["styles"][self.style_choice]["accent_color_mid"],
					bg = self.gui_params["styles"][self.style_choice]["accent_color_mid"],
					foreground = self.gui_params["styles"][self.style_choice]["text"]
				)
			elif isinstance(widget, Scrollbar): widget.configure(
				background = self.gui_params["styles"][self.style_choice]["accent_color_mid"]
			)
			elif isinstance(widget, Listbox):
				widget.configure(
					selectbackground = self.gui_params["styles"][self.style_choice]["accent_color_mid"],
					selectforeground = self.gui_params["styles"][self.style_choice]["text"]
				)
			elif isinstance(widget, OptionMenu):
				widget.configure(
					bg = self.gui_params["styles"][self.style_choice]["accent_color_mid"],
					activebackground = self.gui_params["styles"][self.style_choice]["accent_color_light"]
				)
			else: self.change_style(widget)
		self.ttk_style.map(
			'Treeview',
			background = [('selected', self.gui_params["styles"][self.style_choice]["accent_color_mid"])],
			foreground = [('selected', "#000000")]
		)

	def change_style_live(self, themeString):
		"""This calls the change_style function to enable theme switching in the menu bar."""
		if GUI_debug >= 3: print("change_style_live(themeString = %s)"%(themeString))
		self.style_choice = themeString
		self.change_style(self.topwindow)

	def reload_modules(self):
		"""
		This removes the backend modules (+external modules) and then re-imports them.
		!!! It does not reload the libraries that the modules import.
		e.g. SpaCy, NLTK are NOT reloaded.
		"""

		known = self.backend_API.known_authors
		unknown = self.backend_API.unknown_docs

		sys_modules_pop = [m for m in sys_modules if (
				"generics.modules" in m or "GUI_unified_tabs" in m or "run_experiment" in m or
				"AnalysisMethod" in m or "Canonicizer" in m or "DistanceFunction" in m or
				"EventCulling" in m or "EventDriver" in m or "Embedding" in m or
				"MultiprocessLoading" in m or ("API" in m and "manager" not in m)
			)
		]
		for m in sys_modules_pop: sys_modules.pop(m)
		# sys_modules.pop("backend.API")

		del self.backend_API
		del self.generated_widgets
		collect_garbage()

		import util.MultiprocessLoading as MultiprocessLoading
		from backend.GUI import GUI_unified_tabs
		from backend.API import API
		if platform != "win32" and not TEST_WIN:
			from backend import run_experiment
		else:
			if __name__ == "backend.GUI.GUI2":
				from backend import API_manager

		self.backend_API = API("place-holder")

		self.backend_API.known_authors = known
		self.backend_API.unknown_docs = unknown

		self._unified_tabs()
		self._load_modules_to_GUI()
		self.change_style(self.topwindow)

	def test_run(self):
		"""It initializes the GUI in the background but doesn't show it. Good for testing."""
		print("Loading API")
		from backend.API import API
		self.backend_API = API("place-holder")
		print("Loading GUI")
		self.gui()
		print("done")
		return


	def run(self):
		# open a loading window so the app doesn't appear frozen.
		pipe_from, pipe_to = Pipe(duplex=True)
		if __name__ == "backend.GUI.GUI2":
			p = Process(target=MultiprocessLoading.splash, args=(pipe_to,))
			p.start()
		else:
			print("Please run PyGAAP.py instead of the GUI directly.")

		pipe_from.send("Loading API")
		# LOCAL IMPORTS
		from backend.API import API
		###############################
		#### BACKEND API ##############
		self.backend_API = API("place-holder")
		###############################
		###############################
		pipe_from.send("Starting GUI")
		self.gui()
		pipe_from.send(-1)
		pipe_from.close()
		self.topwindow.mainloop()
