# this is closely coupled with GUI2.py.
# This file is separate from GUI2.py for readability only.


from tkinter import *
from tkinter import ttk

# This function creates canonicizers, event drivers, event culling, and analysis methods tabs.
def create_module_tab(tab_frame: Frame, available_content: list, parameters_content: str = None, **extra):
	"""
	creates a tab of available-buttons-selected-description tab.
	See PyGAAP_developer_manual.md for list of major widgets/frames.
	tab_frame: the top-level frame in the notebook tab
	available_content: list of label texts for the available modules to go in.
	button_functions: list of buttons in the middle frame
	selected_content: list of names of listboxes for the selected modules to go in.
	parameters_content: governs how the parameters frame is displayed
	description_content: governs how the descriptions frame is displayed.
	"""
	assert len(set(available_content)) == len(available_content), \
		"Bug: create_modules_tab: available_content can't have repeated names.\n"
		# can't have more than one "available" listbox with the same name for

	list_of_functions = extra.get("list_of_functions")
	assert list_of_functions != None, "Functions missing for module tabs"

	dpi_setting = extra.get("dpi_setting")
	assert dpi_setting != None, "DPI settings missing. Was it read from gui_params.json?"

	backend_API = extra.get("backend_API")
	assert backend_API != None, "API missing from module creating function."

	topwin = extra.get("topwindow")
	assert topwin != None, '"topwindow" object missing from module creating function.'

	RP_listbox = extra.get("RP_listbox")
	# this is the listbox in the "Review and process" page to update when
	# the user adds a module in previous pages.

	# Layer 0
	objects = dict() # objects in the frame
	tab_frame.columnconfigure(0, weight = 1)
	tab_frame.rowconfigure(0, weight = 1)

	topheight = 0.7
	bottomheight = 1-topheight
	
	objects["top_frame"] = Frame(tab_frame)
	objects["top_frame"].place(relx = 0, rely = 0, relwidth = 1, relheight = topheight)

	# Layer 1: main frames
	objects["available_frame"] = Frame(objects["top_frame"])
	objects["available_frame"].place(relx = 0, rely = 0, relwidth = 0.3, relheight = 1)

	objects["buttons_frame"] = Frame(objects["top_frame"])
	objects["buttons_frame"].place(relx = 0.3, rely = 0, relwidth = 0.1, relheight = 1)

	objects["selected_frame"] = Frame(objects["top_frame"])
	objects["selected_frame"].place(relx = 0.4, rely = 0, relwidth = 0.3, relheight = 1)

	objects["parameters_frame"] = Frame(objects["top_frame"])
	objects["parameters_frame"].place(relx = 0.7, rely = 0, relwidth = 0.3, relheight = 1)

	objects["description_frame"] = Frame(tab_frame)
	objects["description_frame"].place(relx = 0, rely = topheight, relheight = bottomheight, relwidth = 1)

	# Layer 2: objects in main frames
	counter = 0
	objects["available_listboxes"] = []
	# each entry in objects["available_listboxes"]:
	# [frame, label, listbox, scrollbar]
	objects["available_frame"].columnconfigure(0, weight = 1)

	listboxAvList = [] # list of "available" listboxes to pass into select_modules() later.
	for name in available_content:
		# "Available" listboxes
		objects["available_listboxes"].append(
			[Frame(objects["available_frame"])]
		)
		objects["available_listboxes"][-1][0].grid(row = counter, column = 0, sticky = "swen")

		objects["available_frame"].rowconfigure(counter, weight = 1)
		objects["available_frame"].rowconfigure(counter + 1, weight = 0)

		# add a search box.
		objects["search_entry"] = Entry(objects["available_frame"])
		objects["search_entry"].grid(row = counter + 1, sticky = "swen")

		objects["available_listboxes"][-1].append(
			Label(objects["available_listboxes"][-1][0], text = name, font = ("Helvetica", 15))
		)
		objects["available_listboxes"][-1][1].pack(pady = (10, 5), side = TOP, anchor = NW)

		objects["available_listboxes"][-1].append(
			Listbox(objects["available_listboxes"][-1][0], exportselection = False)
		)
		objects["available_listboxes"][-1][2].pack(expand = True, fill = BOTH, side = LEFT)
		listboxAvList.append(objects["available_listboxes"][-1][2])

		objects["available_listboxes"][-1].append(
			Scrollbar(objects["available_listboxes"][-1][0],
			width = dpi_setting["dpi_scrollbar_width"], command = objects["available_listboxes"][-1][2].yview)
		)
		objects["available_listboxes"][-1][3].pack(side = RIGHT, fill = BOTH)
		objects["available_listboxes"][-1][2].config(
			yscrollcommand = objects["available_listboxes"][-1][3].set
		)

		counter += 1   
	
	objects["selected_listboxes"] = []
	objects["selected_listboxes"].append([Frame(objects["selected_frame"])])
	objects["selected_listboxes"][-1][0].pack(expand = True, fill = BOTH)		

	objects["selected_listboxes"][-1].append(
		Label(objects["selected_listboxes"][-1][0],
		text = "Selected", font = ("Helvetica", 15))
	)
	objects["selected_listboxes"][-1][1].pack(pady = (10, 5), side = TOP, anchor = NW)

	if parameters_content == "AnalysisMethods":
		# for analysis methods, use a Treeview object to display selections.
		objects["selected_listboxes"][-1].append(ttk.Treeview(objects["selected_listboxes"][-1][0],
			columns = ("AM", "DF")))
		objects["selected_listboxes"][-1][2].column("#0", width = 0, stretch = NO)
		objects["selected_listboxes"][-1][2].heading("AM", text = "Method", anchor = W)
		objects["selected_listboxes"][-1][2].heading("DF", text = "Distance", anchor = W)
		objects["selected_listboxes"][-1][2].pack(expand = True, fill = BOTH, side = LEFT)

		objects["selected_listboxes"][-1].append(
			Scrollbar(objects["selected_listboxes"][-1][0], width = dpi_setting["dpi_scrollbar_width"],
			command = objects["selected_listboxes"][-1][2].yview))
		objects["selected_listboxes"][-1][3].pack(side = RIGHT, fill = BOTH)
		objects["selected_listboxes"][-1][2].config(yscrollcommand = objects["selected_listboxes"][-1][3].set)

	else:
		# for canonicizers, event cullers/drivers, use a Listbox to display selections.
		objects["selected_listboxes"][-1].append(Listbox(objects["selected_listboxes"][-1][0]))
		objects["selected_listboxes"][-1][2].pack(expand = True, fill = BOTH, side = LEFT)

		objects["selected_listboxes"][-1].append(
			Scrollbar(objects["selected_listboxes"][-1][0], width = dpi_setting["dpi_scrollbar_width"],
			command = objects["selected_listboxes"][-1][2].yview))
		objects["selected_listboxes"][-1][3].pack(side = RIGHT, fill = BOTH)
		objects["selected_listboxes"][-1][2].config(yscrollcommand = objects["selected_listboxes"][-1][3].set)

	Label(objects["buttons_frame"], text = "", height = 2).pack()
	# empty label to create space above buttons
	counter = 0




	if parameters_content == "Canonicizers":
		extra.get("canonicizers_format")
		extra.get("canonicizers_format").set("All")
		canonicizer_format_options = ["All", "Generic", "Doc", "PDF", "HTML"]
		objects["Canonicizers_format"] = OptionMenu(objects["buttons_frame"],
			extra.get("canonicizers_format"), *canonicizer_format_options)
		objects["Canonicizers_format"].config(width = dpi_setting["dpi_option_menu_width"])
		objects["Canonicizers_format"].pack(anchor = W)
		counter = 1



	objects["buttons_add"] = Button(
		objects["buttons_frame"], width = "11", text = ">>Add", anchor = 's',
		command = lambda:list_of_functions["select_modules"](
			listboxAvList,
			[objects["selected_listboxes"][0][2], RP_listbox],
			"add",
			module_type = parameters_content
			)
		)
	objects["buttons_add"].pack(anchor = CENTER, fill = X)

	objects["buttons_remove"] = Button(
		objects["buttons_frame"], width = "11", text = "<<Remove", anchor = 's',
		command = lambda:list_of_functions["select_modules"](
			None, [objects["selected_listboxes"][0][2], RP_listbox], "remove",
			module_type = parameters_content,
			)
		)
	objects["buttons_remove"].pack(anchor = CENTER, fill = X)

	objects["buttons_clear"] = Button(
		objects["buttons_frame"], width = "11", text = "Clear", anchor = 's',
		command = lambda:list_of_functions["select_modules"](
			None,
			[objects["selected_listboxes"][0][2], RP_listbox],
			"clear",
			module_type = parameters_content,
			)
		)
	objects["buttons_clear"].pack(anchor = CENTER, fill = X)


	objects["description_label"] = Label(
		objects["description_frame"], text = "Description", font = ("helvetica", 15), anchor = 'nw'
	)
	objects["description_label"].pack(anchor = NW, pady = (20, 5))
	objects["description_box"] = Text(
		objects["description_frame"], bd = dpi_setting["dpi_description_box_border"],
		relief = "groove", bg = topwin.cget("background"), state = DISABLED
	)
	objects["description_box"].pack(fill = BOTH, expand = True, side = LEFT)
	objects["description_box_scrollbar"] = Scrollbar(
		objects["description_frame"], width = dpi_setting["dpi_scrollbar_width"], command = objects["description_box"].yview
	)
	objects["description_box"].config(yscrollcommand = objects["description_box_scrollbar"].set)
	objects["description_box_scrollbar"].pack(side = LEFT, fill = BOTH)

	if  parameters_content != "AnalysisMethods":
		displayed_parameters = extra.get("displayed_parameters")
		objects['parameters_label'] = Label(
			objects["parameters_frame"], text = "Parameters", font = ("helvetica", 15), anchor = NW
		)
		objects['parameters_label'].pack(pady = (10, 5),anchor = W)

		objects['displayed_parameters_frame'] = Frame(objects["parameters_frame"])
		objects['displayed_parameters_frame'].pack(padx = 20, pady = 20)


		objects["selected_listboxes"][-1][2].bind("<<ListboxSelect>>",
			lambda event, frame = objects['displayed_parameters_frame'],
			lb = objects["selected_listboxes"][-1][2],
			dp = displayed_parameters:
			list_of_functions["find_parameters"](frame, lb, dp, module_type = parameters_content), add = "+"
		)
		objects["selected_listboxes"][-1][2].bind("<<Unmap>>",
			lambda event, frame = objects['displayed_parameters_frame'],
			lb = objects["selected_listboxes"][-1][2],
			dp = displayed_parameters:
			list_of_functions["find_parameters"](frame, lb, dp, module_type = parameters_content), add = "+"
		)
			
	else:
		displayed_parameters = extra.get("displayed_parameters")
		objects['parameters_label'] = Label(
			objects["parameters_frame"], text = "Parameters", font = ("helvetica", 15), anchor = NW
		)
		objects['parameters_label'].pack(pady = (10, 5),anchor = W)

		objects['displayed_parameters_frame'] = Frame(objects["parameters_frame"])
		objects['displayed_parameters_frame'].pack(padx = 20, pady = 20)
		# bind treeview widget so the description updates when an item is selected.
		objects["selected_listboxes"][0][2].bind("<<TreeviewSelect>>",
			lambda event, d = objects["description_box"],
			lb = objects["selected_listboxes"][0][2],
			di = backend_API.analysisMethods:
			list_of_functions["find_description"](d, lb, di), add = "+"
		)
		
		objects["selected_listboxes"][-1][2].bind("<<TreeviewSelect>>",\
			lambda event, frame = objects['displayed_parameters_frame'],
			lb = objects["selected_listboxes"][-1][2],
			dp = displayed_parameters:
			list_of_functions["find_parameters"](frame, lb, dp, module_type = parameters_content), add = "+")


	if parameters_content != "AnalysisMethods":
		API_dict = {
			"Canonicizers": backend_API.canonicizers,
			"EventDrivers": backend_API.eventDrivers,
			"EventCulling": backend_API.eventCulling,
			"NumberConverters": backend_API.numberConverters
		}
		for f in objects["available_listboxes"]:
			f[2].bind("<<ListboxSelect>>",
				lambda event, t = objects["description_box"],
				l = f[2], d = API_dict[parameters_content]:
				list_of_functions["find_description"](t, l, d), add = "+"
			)
		for f in objects["selected_listboxes"]:
			f[2].bind("<<ListboxSelect>>",
				lambda event, t = objects["description_box"],
				l = f[2], d = API_dict[parameters_content]:
				list_of_functions["find_description"](t, l, d), add = "+"
			)
	else:
		objects["available_listboxes"][0][2].bind(
			"<<ListboxSelect>>",
			lambda event,
			lbAv = objects["available_listboxes"][0][2],
			lbOp = objects["available_listboxes"][1][2]:
			list_of_functions["check_DF_listbox"](lbAv, lbOp), add = "+"
		)
		objects["available_listboxes"][0][2].bind(
			"<<ListboxSelect>>",
			lambda event,
			t = objects["description_box"],
			l = objects["available_listboxes"][0][2],
			d = backend_API.analysisMethods:
			list_of_functions["find_description"](t, l, d), add = "+")
		objects["available_listboxes"][1][2].bind(
			"<<ListboxSelect>>",
			lambda event,
			t = objects["description_box"],
			l = objects["available_listboxes"][1][2],
			d = backend_API.distanceFunctions:
			list_of_functions["find_description"](t, l, d), add = "+")

	return objects

