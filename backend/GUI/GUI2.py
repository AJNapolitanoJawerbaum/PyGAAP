# PyGAAP is the Python port of JGAAP,
# Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
#
# See PyGAAP_developer_manual.md for a guide to the structure of the GUI
# and how to add new modules.
# @ author: Michael Fang
#
# Style note: if-print checks using the GUI_debug variable
# are condensed into one line where possible.

GUI_debug = 0
# GUI debug level:
#   0 = no debug info.
#   1 = basic status update.
#   3 = most function calls.
#   info printed to the terminal.

# system modules
from copy import deepcopy
from multiprocessing import Process, Queue, Pipe
from datetime import datetime
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from sys import modules as sys_modules
from sys import exc_info
from sys import platform
from json import load as json_load
from os import listdir as ls
from time import sleep

# local modules
from backend.CSVIO import readDocument, readCorpusCSV, readExperimentCSV
import util.MultiprocessLoading as MultiprocessLoading
from backend.Document import Document
from backend.GUI import GUI_run_experiment
from backend import CSVIO
import Constants


# closely coupled modules
from backend.GUI.GUI_unified_tabs import *

import util.MultiprocessLoading as MultiprocessLoading


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
	known_authors_list: list = []
	# this decides which in the 1-dimensionl listbox is the author...load_save
	#   and therefore can be deleted when using delete author
	# format: [0, -1, -1. -1, 1, -1, ..., 2, -1, ..., 3, -1, ...]
	#   -1 = not author; 
	#   >= 0: author index.

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
	Tab_Documents_KnownAuthors_listbox: Listbox = None

	Tab_RP_Canonicizers_Listbox: Listbox = None
	Tab_RP_EventDrivers_Listbox: Listbox = None
	Tab_RP_EventCulling_Listbox: Listbox = None
	Tab_RP_AnalysisMethods_Listbox: ttk.Treeview = None

	progress_window: Toplevel = None
	error_window: Toplevel = None



	def __init__(self):
		# no internal error handling because fatal error.
		params = json_load(f:=open("./backend/GUI/gui_params.json", "r"))
		self.gui_params = params
		self.gui_params["styles"]["JGAAP_blue"]
		self.backend_API = None
		f.close()

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
			notebook.select(min((notebook.index(notebook.select()) + 1), 5))
		elif mode == "previous":
			notebook.select(max((notebook.index(notebook.select()) - 1), 0))
		elif mode == "choose":
			if tabID >= 0 and tabID <= 5:
				notebook.select(tabID)
		return

	def show_error_window(self, error_text:str, title="Error"):
		self.error_window = None
		self.error_window = Toplevel()
		self.error_window.geometry(self.dpi_setting["dpi_about_page_geometry"])
		self.error_window.title(title)

		Label(self.error_window, text=error_text).pack(padx=30, pady=30)
		return

	def run_experiment(self):
		if GUI_debug >= 3: print("run_experiment()")

		# names of modules in use
		module_names = {
		"canonicizers_names": list(self.Tab_RP_Canonicizers_Listbox.get(0, END)),
		"event_drivers_names": list(self.Tab_RP_EventDrivers_Listbox.get(0, END)),
		"event_cullers_names": list(self.Tab_RP_EventCulling_Listbox.get(0, END)),
		"am_df_names": [self.Tab_RP_AnalysisMethods_Listbox.item(j)["values"]
						for j in list(self.Tab_RP_AnalysisMethods_Listbox.get_children())]
		}

		progress_report_here, progress_report_there = Pipe(duplex=True)
		self.results_queue = Queue()
		experiment = GUI_run_experiment.Experiment(
			self.backend_API, module_names, self.dpi_setting, progress_report_there, self.results_queue
		)

		MultiprocessLoading.process_window(
			self.dpi_setting["dpi_process_window_geometry"],
			"determinate",
			progress_report_here,
			starting_text="Processing",
			progressbar_length=self.dpi_setting["dpi_progress_bar_length"],
			end_run=self.display_results
		)


		self.experiment_process = Process(target=experiment.run_experiment)
		self.experiment_process.start()

		return


	def display_results(self):
		"""Displays results in new window"""
		# show process results

		results_text = self.results_queue.get()

		if results_text.strip() == "":
			print("no results")
			return

		self.status_update("")
		self.results_window = Toplevel()
		self.results_window.title("Results")
		self.results_window.geometry(self.dpi_setting["dpi_process_window_geometry"])
		
		self.results_window.bind("<Destroy>", lambda event, b = "":self.status_update(b))

		
		# create space to display results, release focus of process window.
		results_display = Text(self.results_window)
		results_display.pack(fill = BOTH, expand = True, side = LEFT)
		results_display.insert(END, results_text)
		#results_display.config(state = DISABLED)

		results_scrollbar = Scrollbar(self.results_window,
									width = self.dpi_setting["dpi_scrollbar_width"],
									command = results_display.yview)
		results_display.config(yscrollcommand = results_scrollbar.set)
		results_scrollbar.pack(side = LEFT, fill = BOTH)
		self.results_window.geometry(self.dpi_setting["dpi_process_window_geometry_finished"])
		self.results_window.title(str(datetime.now()))

		self.change_style(self.results_window)

		return


	def process_check(
			self,
			check_listboxes: list,
			check_labels: list,
			process_button: Button,
			# click: bool = False
		):
		if GUI_debug >= 3: print("process_check()")
		all_set = True
		# first check if the listboxes in check_listboxes are empty. If empty
		process_button.config(state = NORMAL, text = "Process")
		for lb_index in range(len(check_listboxes)):
			try: size = len(check_listboxes[lb_index].get_children())
			except AttributeError: size = check_listboxes[lb_index].size()
			if size == 0:
				check_labels[lb_index].config(
					fg = "#e24444",
					activeforeground = "#e24444")
				all_set = False
				process_button.config(
					fg = "#333333",
					state = DISABLED,
					text = "Process [missing parameters]",
					activebackground = "light grey", bg = "light grey")
				# if something is missing
			else: # if all is ready
				check_labels[lb_index].config(fg = "black", activeforeground = "black")
		process_button.config(fg = "black")
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
				self.statusbar_label.after(20,
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

	def authors_list_updater(self, listbox):
		"""This updates the ListBox from the self.backend_API.known_authors python-list"""
		listbox.delete(0, END)
		if GUI_debug >= 3: print("authors_list_updater()")
		self.known_authors_list = []
		for author_list_index in range(len(self.backend_API.known_authors)):
			listbox.insert(END, self.backend_API.known_authors[author_list_index][0])
			listbox.itemconfig(END, 
				background = self.gui_params["styles"][self.style_choice]["accent_color_light"],
				selectbackground = self.gui_params["styles"][self.style_choice]["accent_color_mid"])
			self.known_authors_list += [author_list_index]
			for document in self.backend_API.known_authors[author_list_index][1]:
				listbox.insert(END, document)#Author's documents
				listbox.itemconfig(END, background = "gray90", selectbackground = "gray77")
				self.known_authors_list += [-1]
		return



	def author_save(self, listbox: Listbox, author, documents_list, mode, window=None):
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
						self.authors_list_updater(listbox)
						if window != None: window.destroy()
						return
					author_index += 1
				self.backend_API.known_authors += [[author, list(\
									[file for file in documents_list if type(file) == str]
									)]]
									#no existing author found, add.
				self.authors_list_updater(listbox)
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
						self.authors_list_updater(listbox)
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





	def edit_known_authors(self, authorList, mode):
		"""Add, edit or remove authors
		This opens a window to add/edit authors; does not open a window to remove authors.
			calls author_save (which calls authorListUpdater) when adding/editing author,
		This updates the global self.backend_API.known_authors list.
		"""
		#authorList: the listbox that displays known authors in the topwindow.

		if GUI_debug >= 3: print("edit_known_authors(mode = %s)"%(mode))
		if mode == "add":
			title = "Add Author"
		elif mode == 'edit':
			try:
				authorList.get(authorList.curselection())
				title = "Edit Author"
				selected = int(authorList.curselection()[0])
				if self.known_authors_list[selected] == -1:
					self.status_update("Select the author instead of the document.")
					print("edit author: select the author instead of the document")
					return
				else:
					author_index = self.known_authors_list[selected] #gets the index in the 2D list
					insert_author = self.backend_API.known_authors[author_index][0] #original author name
					insert_docs = self.backend_API.known_authors[author_index][1] #original list of documents
			except TclError:
				self.status_update("No author selected.")
				if GUI_debug > 0:
					print("edit author: no author selected")
				return

		elif mode == "remove":#remove author does not open a window
			try:
				selected = int(authorList.curselection()[0])
				#this gets the listbox selection index
				if self.known_authors_list[selected] == -1:
					self.status_update("Select the author instead of the document.")
					print("remove author: select the author instead of the document")
					return
				else:
					author_index = self.known_authors_list[selected]
					#This gets the index in self.backend_API.known_authors nested list
					if author_index >= len(self.backend_API.known_authors)-1:
						self.backend_API.known_authors = self.backend_API.known_authors[:author_index]
					else:
						self.backend_API.known_authors = self.backend_API.known_authors[:author_index] \
							+ self.backend_API.known_authors[author_index + 1:]
					self.authors_list_updater(authorList)

			except (TclError, IndexError):
				self.status_update("No author selected.")
				if GUI_debug > 0:
					print("remove author: nothing selected")
				return
			return
		elif mode == "clear":
			authorList.delete(0, END)
			self.backend_API.known_authors = []
			self.known_authors_list = []
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
			= lambda:self.author_save(authorList,
									author_name_entry.get(),
									author_listbox.get(0, END),
									mode,
									self.author_window))
		elif mode == "edit":
			author_ok_button.configure(command
			= lambda:self.author_save(authorList,
									[insert_author, author_name_entry.get()],
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

	def load_aaac(self, problem: str):
		"""Loads AAAC problems"""
		# problem: "problem" + capital character.
		corpus_list = CSVIO.readCorpusCSV(self.gui_params["aaac_problems_path"]+'%s/load%s.csv' % (problem, problem[-1]))
		if GUI_debug >= 3: print("problem %s" % problem)
		unknown = [Document(x[0], x[2], "", x[1]) for x in corpus_list if x[0] == ""]
		known = [Document(x[0], x[2], "", x[1]) for x in corpus_list if x[0] != ""] + [Document("", "", "", "")]

		# add unknown docs
		for doc in unknown:
			self._edit_unknown_docs("autoadd", add_list=unknown)

		self.edit_known_authors(self.Tab_Documents_KnownAuthors_listbox, "clear")

		# add known docs
		this_author = ""
		this_author_list = []
		for doc in known:
			if doc.author != this_author:
				if this_author != "":
					self.author_save(self.Tab_Documents_KnownAuthors_listbox, this_author, this_author_list, "add")
				this_author = doc.author
				this_author_list = [doc.filepath]
			else:
				this_author_list.append(doc.filepath)


	def _review_process_tab(self, tabs):
		#####REVIEW & PROCESS TAB
		#basic frames structure
		Tab_ReviewProcess_Canonicizers = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_Canonicizers.grid(
			row = 0, column = 0, columnspan = 3, sticky = "wens", padx = 10, pady = 10
		)

		Tab_ReviewProcess_EventDrivers = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_EventDrivers.grid(
			row = 1, column = 0, sticky = "wens", padx = 10, pady = 10
		)

		Tab_ReviewProcess_EventCulling = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_EventCulling.grid(
			row = 1, column = 1, sticky = "wens", padx = 10, pady = 10
		)

		Tab_ReviewProcess_AnalysisMethods = Frame(self.tabs_frames["Tab_ReviewProcess"])
		Tab_ReviewProcess_AnalysisMethods.grid(
			row = 1, column = 2, sticky = "wens", padx = 10, pady = 10
		)

		for n in range(3):
			self.tabs_frames["Tab_ReviewProcess"].columnconfigure(n, weight = 1)
		for n in range(2):
			self.tabs_frames["Tab_ReviewProcess"].rowconfigure(n, weight = 1)

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
		Tab_RP_AnalysisMethods_Button = Button(
			Tab_ReviewProcess_AnalysisMethods, text = "Analysis Methods",font = ("helvetica", 16), relief = FLAT,
			command = lambda:self.switch_tabs(tabs, "choose", 4))
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
		Tab_RP_Process_Button = Button(self.tabs_frames["Tab_ReviewProcess"], text = "Process", width = 25)

		# button command see after documents tab.

		Tab_RP_Process_Button.grid(row = 2, column = 0, columnspan = 3, sticky = "se", pady = 5, padx = 20)

		Tab_RP_Process_Button.bind("<Map>",
			lambda event, a = [], lb = [self.Tab_RP_EventDrivers_Listbox, self.Tab_RP_AnalysisMethods_Listbox],
			labels = [Tab_RP_EventDrivers_Button, Tab_RP_AnalysisMethods_Button],
			#button = Tab_RP_Process_Button:self.run_experiment(lb, labels, button)
			button = Tab_RP_Process_Button:self.process_check(lb, labels, button)
		)
		
		Tab_RP_Process_Button.config(\
			command = lambda:self.run_experiment())


	def _documents_tab(self):

		Tab_Documents_Language_label = Label(
			self.tabs_frames["Tab_Documents"],text = "Language", font = ("helvetica", 15), anchor = 'nw'
		)
		Tab_Documents_Language_label.grid(row = 1, column = 0, sticky = 'NW', pady = (10, 5))

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
			self.tabs_frames["Tab_Documents"], analysisLanguage, *analysisLanguageOptions
		)
		Tab_Documents_language_dropdown.config(width = self.dpi_setting["dpi_language_dropdown_width"])
		Tab_Documents_language_dropdown['anchor'] = 'nw'
		Tab_Documents_language_dropdown.grid(row = 2, column = 0, sticky = 'NW')


		analysisLanguage.trace_add("write",
							lambda v1, v2, v3, p = "language", stringvar = analysisLanguage:
							self.set_API_global_parameters(p, stringvar)) # TODO 0


		#documents-unknown authors
		Tab_Documents_UnknownAuthors_label =\
			Label(self.tabs_frames["Tab_Documents"], text = "Unknown Authors", font = ("helvetica", 15), anchor = 'nw')
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
				# command = lambda:self.file_add_remove(
				# 	"Add a document to Unknown Authors", self.Tab_Documents_UnknownAuthors_listbox, False, "add")
				command = lambda: self._edit_unknown_docs("add")
		)
		Tab_Documents_UnknownAuthors_RmvDoc_Button = Button(
			Tab_Documents_doc_buttons, text="Remove Document", width = "16",
			# command = lambda:self.file_add_remove(
			# 	None, self.Tab_Documents_UnknownAuthors_listbox, False, "remove")
			command=lambda: self._edit_unknown_docs("remove")
		)
		Tab_Documents_UnknownAuthors_clear_Button = Button(
			Tab_Documents_doc_buttons, text="Clear Document List", width = "16",
			# command = lambda:self.file_add_remove(
			# 	None, self.Tab_Documents_UnknownAuthors_listbox, False, "remove")
			command=lambda: self._edit_unknown_docs("clear")
		)

		Tab_Documents_UnknownAuthors_AddDoc_Button.grid(row = 1, column = 1, sticky = "W")
		Tab_Documents_UnknownAuthors_RmvDoc_Button.grid(row = 1, column = 2, sticky = "W")
		Tab_Documents_UnknownAuthors_clear_Button.grid(row = 1, column = 3, sticky = "W")

		#documents-known authors
		Tab_Documents_KnownAuthors_label = Label(
			self.tabs_frames["Tab_Documents"], text = "Known Authors", font = ("helvetica", 15), anchor = 'nw'
		)
		Tab_Documents_KnownAuthors_label.grid(row = 7, column = 0, sticky = "W", pady = (10, 5))


		Tab_Documents_KnownAuthors_Frame = Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_KnownAuthors_Frame.grid(row = 8, column = 0, sticky = "wnse")


		self.Tab_Documents_KnownAuthors_listbox = Listbox(Tab_Documents_KnownAuthors_Frame, width = "100")
		Tab_Documents_KnownAuthors_listscroller = Scrollbar(Tab_Documents_KnownAuthors_Frame, width = self.dpi_setting["dpi_scrollbar_width"])

		self.Tab_Documents_KnownAuthors_listbox.config(
			yscrollcommand = Tab_Documents_KnownAuthors_listscroller.set
		)
		Tab_Documents_KnownAuthors_listscroller.config(command = self.Tab_Documents_KnownAuthors_listbox.yview)


		self.Tab_Documents_KnownAuthors_listbox.pack(side = LEFT, fill = BOTH, expand = True)
		Tab_Documents_KnownAuthors_listscroller.pack(side = RIGHT, fill = BOTH, padx = (0, 30))

		#These are known authors
		Tab_Documents_knownauth_buttons = Frame(self.tabs_frames["Tab_Documents"])
		Tab_Documents_knownauth_buttons.grid(row = 9, column = 0, sticky = "W")
		Tab_Documents_KnownAuthors_AddAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Add Author", width = "15",
			command = lambda:self.edit_known_authors(self.Tab_Documents_KnownAuthors_listbox, 'add'))
		Tab_Documents_KnownAuthors_EditAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Edit Author", width = "15",
			command = lambda:self.edit_known_authors(self.Tab_Documents_KnownAuthors_listbox, 'edit'))
		Tab_Documents_KnownAuthors_RmvAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Remove Author", width = "15",
			command = lambda:self.edit_known_authors(self.Tab_Documents_KnownAuthors_listbox, "remove"))
		Tab_Documents_KnownAuthors_ClrAuth_Button = Button(
			Tab_Documents_knownauth_buttons, text = "Clear All", width = "15",
			command = lambda:self.edit_known_authors(self.Tab_Documents_KnownAuthors_listbox, "clear"))

		Tab_Documents_KnownAuthors_AddAuth_Button.grid(row=1, column=1, sticky="W")
		Tab_Documents_KnownAuthors_EditAuth_Button.grid(row=1, column=2, sticky="W")
		Tab_Documents_KnownAuthors_RmvAuth_Button.grid(row=1, column=3, sticky="W")
		Tab_Documents_KnownAuthors_ClrAuth_Button.grid(row=1, column=4, sticky="W")

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
		self.generated_widgets['Canonicizers'] = create_module_tab(
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

		self.Tab_EventDrivers_parameters_displayed = []
		self.generated_widgets['EventDrivers'] = create_module_tab(
			self.tabs_frames["Tab_EventDrivers"],
			["Event Drivers"],
			"EventDrivers",
			displayed_parameters = self.Tab_EventDrivers_parameters_displayed,
			RP_listbox = self.Tab_RP_EventDrivers_Listbox,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)

		self.Tab_EventCulling_parameters_displayed = []
		self.generated_widgets['EventCulling'] = create_module_tab(
			self.tabs_frames["Tab_EventCulling"],
			["Event Culling"],
			"EventCulling",
			displayed_parameters = self.Tab_EventCulling_parameters_displayed,
			RP_listbox = self.Tab_RP_EventCulling_Listbox,
			list_of_functions=self.list_of_functions,
			backend_API=self.backend_API,
			topwindow=self.topwindow,
			dpi_setting=self.dpi_setting)

		self.Tab_AnalysisMethods_parameters_displayed = []
		self.generated_widgets['AnalysisMethods'] = create_module_tab(
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

	#ABOVE ARE THE CONFIGS FOR EACH TAB
	def _bottom_frame(self):

		bottomframe = Frame(self.topwindow, height = 150, width = 570)
		bottomframe.columnconfigure(0, weight = 1)
		bottomframe.rowconfigure(1, weight = 1)
		bottomframe.grid(pady = 10, row = 1, sticky = 'swen')

		for c in range(6):
			bottomframe.columnconfigure(c, weight = 10)

		finish_button = Button(bottomframe, text = "Finish & Review", command = lambda:self.switch_tabs(self.tabs, "choose", 5))
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
		self.statusbar_label.after(3000, lambda:self.status_update("", welcome_message))

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

	def file_dialog(self,
			window_title: str,
			allow_duplicates: bool,
			file_types: list=(("Text File", "*.txt"), ("All Files", "*.*")),
			lift_window = None) -> tuple:
		"""Universal add file function to bring up the explorer window"""
		# window_title is the title of the window,
		# may change depending on what kind of files are added
		# listbox_operate is the listbox object to operate on
		# allow_duplicates is whether the listbox allows duplicates.
		# if listbox does not allow duplicates,
		# item won't be added to the listbox and this prints a message to the terminal.
		# lift_window is the window to go back to focus when the file browser closes
		if GUI_debug >= 3: print("file_dialog(allow_duplicates = %s)", allow_duplicates)
		elif GUI_debug >= 1: print("file_dialog")
		filename = askopenfilename(
			filetypes=file_types,
			title=window_title, multiple=allow_duplicates
		)
		if type(filename) == str: return (filename,)
		else: return filename

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
			add_list = self.file_dialog("Add Unknown Document(s)", True)
			for item in add_list:
				# do not read documents and save content to Document.text. Read only when processing.
				self.backend_API.unknown_docs.append(Document("", item.split("/")[-1], "", item))
				self.Tab_Documents_UnknownAuthors_listbox.insert(END, item)

		elif mode == "autoadd":
			self._edit_unknown_docs("clear")
			add_list = options.get("add_list")
			for item in add_list:
				self.backend_API.unknown_docs.append(item)
			for item in self._docs_to_string_list()["unknown"]:
				self.Tab_Documents_UnknownAuthors_listbox.insert(END, item)


	def _load_modules_to_GUI(self, startup=False):

		# first clear everthing in listboxes.
		# the "DistanceFunctions" Treeview is in the "AnalysisMethods" tkinter frame.
		for module_type in ["Canonicizers", "EventDrivers", "EventCulling"]:
			self.generated_widgets[module_type]["available_listboxes"][0][2].delete(0, END)
			self.generated_widgets[module_type]["selected_listboxes"][0][2].delete(0, END)
		for listbox in [self.Tab_RP_Canonicizers_Listbox, self.Tab_RP_EventDrivers_Listbox, self.Tab_RP_EventCulling_Listbox]:
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
				assert distancefunc != "NA", 'Distance Function cannot have a name of "NA" ' \
				+ '(Reserved for Analysis methods that do not use a distance function).\n' \
				+ 'Please check the file containing the definition of the distance function class, ' \
				+ 'most likely in or imported to DistanceFunction.py,\nand change the return of displayName().'
				self.generated_widgets["AnalysisMethods"]["available_listboxes"][1][2].insert(END, distancefunc)
			for culling in sorted(list(self.backend_API.eventCulling.keys())):
				self.generated_widgets["EventCulling"]["available_listboxes"][0][2].insert(END, culling)
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
			error_text += "\n\nDevelopers: Reload modules by going to \"developers\" -> \"Reload all modules\""
			error_text_field.insert(END, error_text)
			error_window.after(1200, error_window.lift)
			if startup == False: self.status_update("Error while loading modules, see pop-up window.")
			#exc_type, exc_obj, exc_tb = exc_info()
			return
		#######

					

	
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
			except TypeError:
				self.show_error_window(
					"Something went wrong while adding the module.\n\n"
					+ "\n\n".join([str(x) for x in exc_info()[:2]])
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
					.__dict__.get("_NoDistanceFunction_") == True:
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
			%(len(displayed_params), clear))


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
		
		
		# currently only support OptionMenu variables
		param_options = []
		# list of StringVars.
		if type(listbox) == Listbox:
			number_of_modules = len(this_module._variable_options)
		else:
			try:
				df_variables = this_df_module._variable_options
			except AttributeError:
				df_variables = []
			number_of_modules = len(this_module._variable_options) \
							+ len(df_variables)
			number_of_am = len(this_module._variable_options)
		if number_of_modules == 0:
			# if this module does not have parameters to be set, say so.
			displayed_params.append(Label(param_frame,
									text = "No parameters for this module."))
			displayed_params[-1].pack()
		else:
			# if this module has parameters, find and display parameters.
			rowshift = 0
			# this is the row shift for widgets below the second tkinter.Label.
			# It's non-zero for when there are two groups of parameters to display.
			# (Analysis + DF)
			displayed_params.append(Label(param_frame,
										text = str(this_module_name) + ":",
										font = ("Helvetica", 14)))
			displayed_params[-1].grid(row = 0, column = 0, columnspan = 2, sticky = W)
			for i in range(number_of_modules):
				if type(listbox) == Listbox:
					parameter_i = list(this_module._variable_options.keys())[i]
					param_options.append(StringVar(
						value = str(this_module.__dict__.get(parameter_i)))
					)
				elif type(listbox) == ttk.Treeview:
					if i < number_of_am:
						parameter_i = list(this_module._variable_options.keys())[i]
						param_options.append(StringVar(
						value = str(this_module.__dict__.get(parameter_i)))
					)
					else:
						rowshift = 1
						if this_df_module == "NA": break
						parameter_i = list(this_df_module._variable_options.keys())[i - number_of_am]
						param_options.append(StringVar(
						value = str(this_df_module._variable_options[parameter_i]["options"]\
							[this_df_module._variable_options[parameter_i]["default"]]))
					)
				displayed_params.append(Label(param_frame, text = parameter_i))
				displayed_params[-1].grid(row = i + 1 + rowshift, column = 0)

				if this_module._variable_options[parameter_i]["type"] == 'Entry':
					raise NotImplementedError
					# TODO 2 priority low:
					# implement text entry for parameters.
					displayed_params.append(Entry(param_frame))
					displayed_params[-1].insert(
						0, str(parameter_i['options'][parameter_i])
					)
					displayed_params[-1].grid(row = i + 1 + rowshift, column = 1, sticky = W)
				elif this_module._variable_options[parameter_i]["type"] == 'OptionMenu':
					displayed_params.append(
						OptionMenu(
							param_frame, 
							param_options[-1],
							*this_module._variable_options[parameter_i]['options']
						)
					)
					displayed_params[-1].config(width = self.dpi_setting["dpi_option_menu_width"])
					displayed_params[-1].grid(row = i + 1 + rowshift, column = 1, sticky = W)
					param_options[-1].trace_add(("write"),
						lambda v1, v2, v3, stringvar = param_options[-1],
						module = this_module, var = parameter_i:\
							self.set_parameters(stringvar, module, var))
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

	def set_parameters(self, stringvar, module, variable_name):
		"""sets parameters whenever the widget is touched."""
		if GUI_debug >= 3:
			print("set_parameters(module = %s, variable_name = %s)"
			%(module, variable_name))

		value_to = stringvar.get()

		try: # to identify numbers
			value_to = float(value_to)
			# if value is a number, try converting to a number.
			if abs(int(value_to) - value_to) < 0.0000001:
				value_to = int(value_to)
		except ValueError:
			pass
		setattr(module, variable_name, value_to)
		return

	def set_API_global_parameters(self, parameter, stringvar):
		"""Wrapper for backend_API's global parameter setter"""
		self.backend_API.set_global_parameters(parameter, stringvar.get())
		return


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
		multiprocessing_limit_docs = float("inf")
		# See TODO 1.
		# the number of docs before
		# multi-processing is used.

		multiprocessing_limit_analysis = float("inf")
		# See TODO 1.
		# the sum score of the
		# "time-consumingness" of analysis methods
		# before multi-processing is used.

		menubar = Menu(topwindow)
		menu_file = Menu(menubar, tearoff = 0)

		self.Tab_Documents_UnknownAuthors_listbox = None
		self.Tab_Documents_KnownAuthors_listbox = None

		#tkinter menu building goes from bottom to top / leaves to root
		menu_batch_documents = Menu(menu_file, tearoff = 0)#batch documents menu
		menu_batch_documents.add_command(
			label = "Save Documents",
			command = lambda function = "save":
			self.load_save_docs(
				function,
				self.Tab_Documents_UnknownAuthors_listbox,
				self.Tab_Documents_KnownAuthors_listbox
			)
		)
		menu_batch_documents.add_command(
			label="Load Documents",
			command=lambda function = "load":
				self.load_save_docs(
					function,
					self.Tab_Documents_UnknownAuthors_listbox,
					self.Tab_Documents_KnownAuthors_listbox
				)
		)
		menu_batch_documents.add_command(
			label="Clear and load Documents",
			command=lambda function = "load_clear":
				self.load_save_docs(
					function,
					self.Tab_Documents_UnknownAuthors_listbox,
					self.Tab_Documents_KnownAuthors_listbox
				)
		)
		menu_file.add_cascade(
			label = "Batch Documents ***", menu = menu_batch_documents,
			underline = 0
		)

		menu_AAAC_problems = Menu(menu_file, tearoff = 0)
		
		for problem in ls(self.gui_params["aaac_problems_path"]):
			if "problem" in problem and problem[7] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
				menu_AAAC_problems.add_command(label="Problem "+problem[-1], command=lambda p=problem:self.load_aaac(p))

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
		menu_dev.add_command(label="Reload all modules", command=self.reload_modules)
		menu_dev.add_command(label="Show process content", command=self.show_process_content)
		menubar.add_cascade(label="Developer", menu=menu_dev)

		topwindow.config(menu = menubar)
		#bottom of the main window is at the bottom of this file


		#the middle workspace where the tabs are

		workspace = Frame(topwindow, height = 800, width = 570)
		workspace.grid(padx = 10, pady = 5, row = 0, sticky = "nswe")
		workspace.columnconfigure(0, weight = 1)
		workspace.rowconfigure(0, weight = 2)

		self.tabs = ttk.Notebook(workspace)
		self.tabs.pack(pady = 1, padx = 5, expand = True, fill = "both")

		# add tabs
		for t in self.tabs_names:
			self.tabs_frames[t] = Frame(self.tabs, height = self.gui_params["tabheight"], width = self.gui_params["tabwidth"])
			self.tabs_frames[t].pack(fill = 'both', expand = True, anchor = NW)


		self.tabs.add(self.tabs_frames["Tab_Documents"], text = "Documents")
		self.tabs.add(self.tabs_frames["Tab_Canonicizers"], text = "Canonicizers")
		self.tabs.add(self.tabs_frames["Tab_EventDrivers"], text = "Event Drivers")
		self.tabs.add(self.tabs_frames["Tab_EventCulling"], text = "Event Culling")
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
		for entry in range(len(self.known_authors_list)):
			if self.known_authors_list[entry] != -1:
				self.Tab_Documents_KnownAuthors_listbox.itemconfig(
					entry,
					background = self.gui_params["styles"][self.style_choice]["accent_color_light"],
					selectbackground = self.gui_params["styles"][self.style_choice]["accent_color_mid"]
				)
		self.change_style(self.topwindow)

	def reload_modules(self):
		"""
		This removes the backend modules (+external modules) and then re-imports them.
		!!! It does not reload the libraries that the modules import.
		e.g. SpaCy, NLTK are NOT reloaded.
		"""
		for module_type in [
			"generics.AnalysisMethod", "generics.Canonicizer", "generics.DistanceFunction",
			"generics.EventCulling", "generics.EventDriver"
		]:
			for external_module in sys_modules[module_type].external_modules:
				sys_modules.pop(external_module)
			sys_modules.pop(module_type)
		sys_modules.pop("backend.API")
		sys_modules.pop("util.MultiprocessLoading")

		import util.MultiprocessLoading as MultiprocessLoading
		from backend.API import API
		self.backend_API = API("place-holder")
		self._load_modules_to_GUI()

	def show_process_content(self):
		print("self.backend_API.unknown_docs:\n")
		[print(str(d)) for d in self.backend_API.unknown_docs]
		print("self.backend_API.known_authors:\n")
		[print(str(d)) for d in self.backend_API.known_authors]
		print("modules\n" + str(self.backend_API.modulesInUse))
		return


	def test_run(self):
		"""This loads everything but without starting the mainloop or splash screen."""
		from backend.API import API
		self.backend_API = API("place-holder")
		self.gui()

	def run(self):
		# open a loading window so the app doesn't appear frozen.
		pipe_from, pipe_to = Pipe(duplex=True)
		if platform != "win32":
			p = Process(target=MultiprocessLoading.splash, args=(pipe_to,))
			p.start()
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
		#self.load_aaac("problemM")
		self.topwindow.mainloop()



if __name__ == "__main__":
	app = PyGAAP_GUI()
	app.run()
