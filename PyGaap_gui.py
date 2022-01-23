# My attempt at creating a PyGaap GUI. Unfinished, do not redistribute. (no-one wants to see this)
# PyGaap is the Python port of JGAAP, Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
# 
############### !! See PyGaap_gui_functions_map.txt for a rough outline of Tkinter widgets and function calls.
#
versiondate="2022.01.23"
#Michael Fang, Boston University.

debug=0 # debug level. 0 = no debug info. 3 = all function calls

#REQUIRED MODULES BELOW. USE pip OR pip3 IN YOUR TERMINAL TO INSTALL.

from cProfile import label
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.tix import CheckList
from turtle import bgcolor

from dbus import StarterBus

from backend.API import API

topwindow=Tk() #this is the top-level window when you first open PyGAAP
topwindow.title("PyGAAP (GUI)")

topwindow.rowconfigure(0, weight=1)
topwindow.rowconfigure(1, weight=0, minsize=50)
topwindow.columnconfigure(0, weight=1)


################### AESTHETICS
dpi=topwindow.winfo_fpixels('1i')
dpi_setting=None
if dpi>72:
    if debug>=2: print("1x UI scale")
    dpi_setting=1
    topwindow.geometry("1000x670")
    #topwindow.minsize(height=400, width=600)
    scrollbar_width=16
else:
    if debug>=2: print("2x UI scale")
    dpi_setting=2
    topwindow.geometry("2000x1150")
    #topwindow.minsize(height=800, width=1100)
    scrollbar_width=28

if dpi_setting==None: raise ValueError("Unknown DPI setting %s."% (str(dpi_setting)))

accent_color_mid="#c9f6fc"
accent_color_dark="#7eedfc"
accent_color_light="#e0f9fc"
if debug>=3: print("Accent colors:", accent_color_dark, accent_color_mid, accent_color_light)

###############################
#### BACKEND API ##########################
backendAPI=API("docs lmao")
##########################################
###############################

#BELOW ARE UTILITY FUNCTIONS
def todofunc(): #place holder "to-do function"
    print("To-do function")
    return None

statusbar=None
statusbar_label=None
def status_update(displayed_text, conditional=None):
    """
    updates the text in the status bar.
    if conditional is specified: change label if True, don't change if False.
    """
    if debug>=3: print("status_update(%s, condition=%s)" %(displayed_text, conditional))
    global statusbar
    global statusbar_label
    if conditional==None:
        statusbar_label.config(text=displayed_text)
    elif conditional==True:
        statusbar_label.config(text=displayed_text)
    return None

def select_features(ListBoxAv: Listbox, ListBoxOp: list, feature, function: str):
    """Used by Event Drivers, Event culling etc to add/remove/clear selected features.
    Needs to check if feature is already added."""
    #ListBoxAv: "listbox Available", listbox to choose from
    #ListBoxOp: "listbox operate-on", a list of listboxes to modify. Includes the one in the corresponding tab and the
    #   listbox in the Review & Process tab.
    #feature: is the return of listbox.curselection()
    #function: can be "clear", "remove", or "add"
    if function=="clear":
        if debug>1: print("select_features: clear")
        for listboxmember in ListBoxOp:
            listboxmember.delete(0, END)
        #if label != None:
        #    label.configure(text=label["text"]+" ×")
    elif function=="remove":
        if debug>1: print("select_features: remove")
        try:
            for listboxmember in ListBoxOp:
                listboxmember.delete(feature)
                listboxmember.select_set(END)
            
        #    if ListBoxOp[0].size()==0 and label != None:
        #        label.configure(text=label["text"]+" ×")
        except:
            if debug>0:
                print("remove from list: nothing selected or empty list.")
            return None
    elif function=="add":
        if debug>1: print("select_features: add")
        try:
            for listboxmember in ListBoxOp:
                listboxmember.insert(END, ListBoxAv.get(feature))
            #if label != None:
            #    label.configure(text=label["text"][:-2])
        except:
            if debug>0:
                print("add to list: nothing selected")
    else:
        raise ValueError("Bug: All escaped in 'select_features' function.")
    #print(ListBoxOp[0].get(0, ListBoxOp[0].size()))
    return None


def find_parameters(frame_to_update: Frame, listbox: Listbox, displayed_params: list, list_of_params: dict=None, clear: bool=False):
    """find parameters in some features to display and set"""
    # feature: individual event drivers, event culling, or analysis methods.
    # frame_to_update: the tkinter frame that displays the parameters.
    # listbox: the tkinter listbox that has the selected parameters.
    # displayed_params: a list of currently displayed parameter options.
    # list_of_params: list of available parameters for each feature. This will be generated or read from the backend. If None, will use a test list.
    
    # DO NOT ASSIGN NEW list_of_params. ONLY USE LIST METHODS ON THIS.
    if debug>=3: print("find_parameters(frame_to_update=%s, listbox=%s, displayed_params=%s, list_of_params=%s, clear=%s)" %(frame_to_update, listbox, displayed_params, list_of_params, clear))
    if list_of_params==None:
        if debug>=1:
            print("Using place-holder list of parameters.")
        list_of_params={"first": [{"options": range(1, 20), "default": 1, "type": "Entry", "label": "first, param 1"},
            {"options": ["option1", "option2"], "default": 0, "type": "OptionMenu", "label": "first, param 2"}],
            "fifth": [{"options": range(0, 10), "default": 0, "type": "Entry", "label": "fifth, param 1"}]}
        # structure: dictionary of list [features] of dictionaries [parameters]
        # the "default" item is always used as a key to "options".
        # i.e. the default value of an entry is always "options"["default"] and never "default".value.
    
    # first get the parameters to display from list.
    if len(listbox.curselection())>0:
        parameters_to_display=list_of_params.get(listbox.get(listbox.curselection()))
    else: return None
    
    
    for params in displayed_params:
        params.destroy()
    displayed_params.clear()
    if clear==True:
        return None

    param_options=[] # list of StringVar s.

    if parameters_to_display==None: # if this feature does not have parameters to be set
        displayed_params.append(Label(frame_to_update, text="No parameters for this feature."))
        displayed_params[-1].pack()
    else:
        for i in range(len(parameters_to_display)):
            param_options.append(StringVar(value=str(parameters_to_display[i]['options'][parameters_to_display[i]['default']])))
            displayed_params.append(Label(frame_to_update, text=parameters_to_display[i]['label']))
            displayed_params[-1].grid(row=i+1, column=0)

            if parameters_to_display[i]['type']=='Entry':
                displayed_params.append(Entry(frame_to_update))
                displayed_params[-1].insert(0, str(parameters_to_display[i]['options'][parameters_to_display[i]['default']]))
                displayed_params[-1].grid(row=i+1, column=1, sticky=W)
            elif parameters_to_display[i]['type']=='OptionMenu':
                displayed_params.append(OptionMenu(frame_to_update, param_options[-1], *parameters_to_display[i]['options']))
                displayed_params[-1].grid(row=i+1, column=1, sticky=W)
        
        displayed_params.append(Label(frame_to_update, text='Parameters for: '+str(listbox.get(listbox.curselection())), font=("Helvetica", 14)))
        displayed_params[-1].grid(row=0, column=0, columnspan=2, sticky=W)
    frame_to_update.columnconfigure(0, weight=1)
    frame_to_update.columnconfigure(1, weight=3)

    return None



processWindow=None
def process(params: dict, check_listboxes: list, check_labels: list, process_button: Button, click: bool=False):
    """
    Process all input files with the parameters in all tabs.
    input: unknown authors, known authors, all listboxes.
    """
    # check_listboxes: list of listboxes that shouldn't be empty.
    # check_labels: list of labels whose text colors need to be updated upon checking the listboxes.
    if debug>=3: print("process(params=%s, check_listboxes=%s, check_labels=%s, process_button=%s, click=%s)" %(params, check_listboxes, check_labels, process_button, click))
    all_set=True
    # first check if the listboxes in check_listboxes are empty. If empty
    process_button.config(state=NORMAL, text="Process", activebackground=accent_color_light, bg=accent_color_mid)
    for lb_index in range(len(check_listboxes)):
        if check_listboxes[lb_index].size()==0:
            check_labels[lb_index].config(fg="#e24444", activeforeground="#e24444")
            all_set=False
            process_button.config(fg="#333333", state=DISABLED, text="Process [missing parameters]", activebackground="light grey", bg="light grey")
            # if something is missing
        else: # if all is ready
            check_labels[lb_index].config(fg="black", activeforeground="black")
    process_button.config(fg="black")
    if not all_set or click==False:
        return None

    status_update("Starting process...")

    global processWindow

    processWindow=Toplevel()
    processWindow.title("Process Window")
    if dpi_setting==1:
        processWindow.geometry("200x100")
        progressBar=ttk.Progressbar(processWindow, length=200, mode="indeterminate")
    elif dpi_setting==2:
        processWindow.geometry("450x150")
        progressBar=ttk.Progressbar(processWindow, length=400, mode="indeterminate")
    
    progressBar.pack(anchor=CENTER, pady=40)
    processWindow.bind("<Destroy>", lambda event, b="":status_update(b))
    processWindow.grab_set()
    progressBar.start()

    return None




AboutPage=None
def displayAbout():
    global versiondate
    global AboutPage
    """Displays the About Page"""
    if debug>=3: print("displayAbout()")
    try:
        AboutPage.lift()
        return None
    except:
        pass
    AboutPage=Toplevel()
    AboutPage.title("About PyGAAP")
    if dpi_setting==1:
        AboutPage.geometry("600x300")
    elif dpi_setting==2:
        AboutPage.geometry("1200x600")
    AboutPage.resizable(False, False)
    AboutPage_logosource=PhotoImage(file="logo.png")
    AboutPage_logosource=AboutPage_logosource.subsample(2, 2)
    AboutPage_logo=Label(AboutPage, image=AboutPage_logosource)
    AboutPage_logo.pack(side="top", fill="both", expand="yes")

    textinfo="THIS IS AN UNFINISHED VERSION OF PyGAAP GUI.\n\
    Version date: "+versiondate+"\n\
    PyGAAP is a Python port of JGAAP,\n\
    Java Graphical Authorship Attribution Program.\n\
    This is an open-source tool developed by the EVL Lab\n\
    (Evaluating Variation in Language Laboratory)."
    AboutPage_text=Label(AboutPage, text=textinfo)
    AboutPage_text.pack(side='bottom', fill='both', expand='yes')
    AboutPage.mainloop()


Notes_content=""
NotepadWindow=None

def notepad():
    """Notes button window"""
    global Notes_content
    global NotepadWindow
    # prevents spam-spawning. took me way too long to figure this out
    if debug>=3: print("notepad()")
    try:
        NotepadWindow.lift()
    except:
        NotepadWindow=Toplevel()
        NotepadWindow.title("Notes")
        #NotepadWindow.geometry("600x500")
        NotepadWindow_Textfield=Text(NotepadWindow)
        NotepadWindow_Textfield.insert("1.0", str(Notes_content))
        NotepadWindow_SaveButton=Button(NotepadWindow, text="Save & Close", activebackground=accent_color_light, bg=accent_color_mid,\
            command=lambda:Notepad_Save(NotepadWindow_Textfield.get("1.0", "end-1c"), NotepadWindow))
        NotepadWindow_Textfield.pack(padx=7, pady=7, expand=True)
        NotepadWindow_SaveButton.pack(pady=(0, 12), expand=True)
        NotepadWindow.mainloop()
    return None

def Notepad_Save(text, window):
    """saves the contents displayed in the notepad textfield when the button is pressed"""
    global Notes_content
    Notes_content=text
    window.destroy()
    if debug>=3: print("Notepad_Save()")
    return None

def switch_tabs(notebook, mode, tabID=0):
    """called by the next button and the tab lables themselves.
    if called by next button, returns the next tab. if called by tab label click, gets that tab"""
    if debug>=3: print("switch_tabs(mode=%s, tabID=%i)" %(mode, tabID))
    if mode=="next":
        try:
            notebook.select(notebook.index(notebook.select())+1)
            return None
        except:
            return None
    elif mode=="previous":
        try:
            notebook.select(notebook.index(notebook.select())-1)
            return None
        except:
            return None
    elif mode=="choose":
        try:
            notebook.select(tabID)
            return None
        except:
            return None

def addFile(WindowTitle, ListboxOp, AllowDuplicates, liftwindow=None):
    """Universal add file function to bring up the explorer window"""
    #WindowTitle is the title of the window, may change depending on what kind of files are added
    #ListboxOp is the listbox object to operate on
    #AllowDuplicates is whether the listbox allows duplicates.
    #if listbox does not allow duplicates, item won't be added to the listbox and this prints a message to the terminal.
    #liftwindow is the window to go back to focus when the file browser closes
    if debug>=1: print("addFile")
    elif debug>=3: print("addFile(ListboxOp=%s, AllowDuplicates=%s)", ListboxOp, AllowDuplicates)
    filename=askopenfilename(filetypes=(("Text File", "*.txt"), ("All Files", "*.*")), title=WindowTitle)
    if liftwindow != None:
        liftwindow.lift(topwindow)
    if AllowDuplicates and filename !="" and len(filename)>0:
        ListboxOp.insert(END, filename)
    else:
        for fileinlist in ListboxOp.get(0, END):
            if fileinlist==filename:
                if debug>0:
                    print("Add document: file already in list")
                liftwindow.lift()
                return None
        if filename != None and filename !="" and len(filename)>0:
            ListboxOp.insert(END, filename)

    if liftwindow != None:
        liftwindow.lift()
    return None



KnownAuthors=[]
# KnownAuthors list format: [[author, [file-directory, file-directory]], [author, [file-directory, file directory]]]
KnownAuthorsList=[]
# this decides which in the 1-dimensionl listbox is the author and therefore can be deleted when using delete author
# format: [0, -1, -1. -1, 1, -1, ..., 2, -1, ..., 3, -1, ...] -1=not author; >=0: author index.

def authorsListUpdater(listbox):
    """This updates the ListBox from the KnownAuthors python-list"""
    global KnownAuthors
    global KnownAuthorsList
    listbox.delete(0, END)
    if debug>=3: print("authorsListUpdater()")
    KnownAuthorsList=[]
    for authorlistindex in range(len(KnownAuthors)):#Authors
        listbox.insert(END, KnownAuthors[authorlistindex][0])
        listbox.itemconfig(END, background="light cyan", selectbackground="sky blue")
        KnownAuthorsList+=[authorlistindex]
        for document in KnownAuthors[authorlistindex][1]:
            listbox.insert(END, document)#Author's documents
            listbox.itemconfig(END, background="gray90", selectbackground="gray77")
            KnownAuthorsList+=[-1]
    return None


def authorSave(window, listbox, author, documentsList, mode):
    """This saves author when adding/editing to the KnownAuthors list. Then uses authorsListUpdater to update the listbox
    """
    #Listbox: the authors listbox.
    #author: 
    #       "ADD MODE": the author's name entered in authorsList window
    #       "EDIT MODE": [original author name, changed author name]
    #documentsList: list of documents entered in the listbox in the authorsList window
    #mode: add or edit
    global KnownAuthors
    if debug>=3: print("authorSave(mode=%s)" %(mode))
    if mode=="add":
        if (author != None and author.strip() !="") and (documentsList !=None and len(documentsList)!=0):  
            AuthorIndex=0
            while AuthorIndex<len(KnownAuthors):#check if author already exists
                if KnownAuthors[AuthorIndex][0]==author:#when author is already in the list, merge.
                    KnownAuthors[AuthorIndex][1]=KnownAuthors[AuthorIndex][1]+list([doc for doc in documentsList if doc not in KnownAuthors[AuthorIndex][1]])
                    authorsListUpdater(listbox)
                    window.destroy()
                    return None
                AuthorIndex+=1
            KnownAuthors+=[[author, list([file for file in documentsList if type(file)==str])]]#no existing author found, add.
            authorsListUpdater(listbox)
        window.destroy()
        return None
    elif mode=='edit':
        if (author[1] != None and author[1].strip() !="") and (documentsList !=None and len(documentsList)!=0):
            AuthorIndex=0
            while AuthorIndex<len(KnownAuthors):
                if KnownAuthors[AuthorIndex][0]==author[0]:
                    KnownAuthors[AuthorIndex]=[author[1], documentsList]
                    authorsListUpdater(listbox)
                    window.destroy()
                    return None
                AuthorIndex+=1
            print("coding error: editing author: list of authors and documents changed unexpectedly when saving")
            return None
    else:
        print("coding error: unknown parameter passed to 'authorSave' function: ", str(mode))
    window.destroy()
    return None

AuthorWindow=None

def authorsList(authorList, mode):
    """Add, edit or remove authors
    This updates the global KnownAuthors list.
    This opens a window to add/edit authors; does not open a window to remove authors
    """
    #authorList: the listbox that displays known authors in the topwindow.
    #authorList calls authorSave (which calls authorListUpdater) when adding/editing author
    #
    global KnownAuthors
    global KnownAuthorsList
    if debug>=3: print("authorsList(mode=%s)"%(mode))
    if mode=="add":
        title="Add Author"
        mode='add'
    elif mode=='edit':
        try:
            authorList.get(authorList.curselection())
            title="Edit Author"
            mode='edit'
            selected=int(authorList.curselection()[0])
            if KnownAuthorsList[selected]==-1:
                print("edit author: select the author instead of the document")
                return None
            else:
                AuthorIndex=KnownAuthorsList[selected]#gets the index in the 2D list
                insertAuthor=KnownAuthors[selected][0]#original author name
                insertDocs=KnownAuthors[selected][1]#original list of documents
        except:
            if debug>0:
                print("edit author: nothing selected")
            return None

    elif mode=="remove":#remove author does not open a window
        try:
            selected=int(authorList.curselection()[0])#this gets the listbox selection index
            if KnownAuthorsList[selected]==-1:
                print("remove author: select the author instead of the document")
                return None
            else:
                AuthorIndex=KnownAuthorsList[selected]#This gets the index in KnownAuthors nested list
                if AuthorIndex>=len(KnownAuthors)-1:
                    KnownAuthors=KnownAuthors[:AuthorIndex]
                else:
                    KnownAuthors=KnownAuthors[:AuthorIndex]+KnownAuthors[AuthorIndex+1:]
                authorsListUpdater(authorList)

        except:
            if debug>0:
                print("remove author: nothing selected")
            return None
        return None
    else:
        assert mode=="add" or mode=="remove" or mode=="edit", "bug: Internal function 'authorsList' has an unknown mode parameter "+str(mode)
        
        return None

    global AuthorWindow
    
    AuthorWindow=Toplevel()
    AuthorWindow.grab_set()#Disables main window when the add/edit author window appears
    AuthorWindow.title(title)
    if dpi_setting==1:
        AuthorWindow.geometry("550x340")
    elif dpi_setting==2:
        AuthorWindow.geometry("1170x590")


    AuthorNameLabel=Label(AuthorWindow, text="Author", font="bold", padx=10).grid(row=1, column=1, pady=7, sticky="NW")
    AuthorFilesLabel=Label(AuthorWindow, text="Files", font="bold", padx=10).grid(row=2, column=1, pady=7, sticky="NW")

    AuthorNameEntry=Entry(AuthorWindow, width=40)
    if mode=="edit":
        AuthorNameEntry.insert(END, insertAuthor)
    AuthorNameEntry.grid(row=1, column=2, pady=7, sticky="NW")

    AuthorListbox=Listbox(AuthorWindow, height=12, width=60)
    if mode=="edit":
        for j in insertDocs:
            AuthorListbox.insert(END, j)
    AuthorListbox.grid(row=2, column=2, sticky="NW")

    AuthorButtonsFrame=Frame(AuthorWindow)
    
    AuthorAddDocButton=Button(AuthorButtonsFrame, text="Add Document", activebackground=accent_color_light, bg=accent_color_mid,\
        command=lambda:addFile("Add Document For Author", AuthorListbox, False, AuthorWindow))
    AuthorAddDocButton.grid(row=1, column=1)
    AuthorRmvDocButton=Button(AuthorButtonsFrame, text="Remove Document", activebackground=accent_color_light, bg=accent_color_mid,\
        command=lambda:select_features(None, AuthorListbox, AuthorListbox.curselection(), 'remove'))
    AuthorRmvDocButton.grid(row=1, column=2)
    AuthorButtonsFrame.grid(row=3, column=2, sticky='NW')

    AuthorBottomButtonsFrame=Frame(AuthorWindow)
    #OK button functions differently depending on "add" or "edit".
    AuthorOKButton=Button(AuthorBottomButtonsFrame, text="OK", activebackground=accent_color_light, bg=accent_color_mid,)
    if mode=="add":
        AuthorOKButton.configure(command=lambda:authorSave(AuthorWindow, authorList, AuthorNameEntry.get(), AuthorListbox.get(0, END), mode))
    elif mode=="edit":
        AuthorOKButton.configure(command=lambda:authorSave(AuthorWindow, authorList, [insertAuthor, AuthorNameEntry.get()], AuthorListbox.get(0, END), mode))

    AuthorOKButton.grid(row=1, column=1, sticky="W")
    AuthorCancelButton=Button(AuthorBottomButtonsFrame, text="Cancel", activebackground=accent_color_light, bg=accent_color_mid, command=lambda:AuthorWindow.destroy())
    AuthorCancelButton.grid(row=1, column=2, sticky="W")
    AuthorBottomButtonsFrame.grid(row=4, column=2, pady=7, sticky="NW")
    
    AuthorWindow.mainloop()
    return None

#ABOVE ARE UTILITY FUNCTIONS

#Test List for features
testfeatures=["first", "second", "third", "fourth", 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth']\
    +list(range(50))
# test dictionary of feature's parameters. keys are feature index in the list above (test list of features.)
testfeatures_parameters={"first": ["param 1", "param 2"], "fifth": ["param 1", "param 2", "param 3"], "eleventh": ["param 1", "param 2"]}

menubar=Menu(topwindow)#adds top menu bar
filemenu=Menu(menubar, tearoff=0)

#tkinter menu building goes from bottom to top / leaves to root
BatchDocumentsMenu=Menu(filemenu, tearoff=0)#batch documents menu
BatchDocumentsMenu.add_command(label="Save Documents", command=todofunc)
BatchDocumentsMenu.add_command(label="Load Documents", command=todofunc)
filemenu.add_cascade(label="Batch Documents", menu=BatchDocumentsMenu, underline=0)

AAACProblemsMenu=Menu(filemenu, tearoff=0)#problems menu
AAACProblemsMenu.add_command(label="Problem 1", command=todofunc)
filemenu.add_cascade(label="AAAC Problems", menu=AAACProblemsMenu, underline=0)

filemenu.add_separator()#file menu
filemenu.add_command(label="Exit", command=topwindow.destroy)
menubar.add_cascade(label="File", menu=filemenu)

helpmenu=Menu(menubar, tearoff=0)#help menu
helpmenu.add_command(label="About...", command=displayAbout)
menubar.add_cascade(label="Help", menu=helpmenu)

topwindow.config(menu=menubar)
#bottom of the main window is at the bottom of this file


#the middle workspace where the tabs are

workspace=Frame(topwindow, height=800, width=570)
workspace.grid(padx=10, pady=5, row=0, sticky="nswe")
workspace.columnconfigure(0, weight=1)
workspace.rowconfigure(0, weight=2)

tabs=ttk.Notebook(workspace)
tabs.pack(pady=1, padx=5, expand=True, fill="both")

#size for all the main tabs.
tabheight=570
tabwidth=1000

Tabs_names=["Tab_Documents", "Tab_Canonicizers", "Tab_EventDrivers", "Tab_EventCulling", "Tab_AnalysisMethods", "Tab_ReviewProcess"]
Tabs_Frames=dict() # this stores the main Frame objects for all the tabs.

#below is the tabs framework
for t in Tabs_names:
    Tabs_Frames[t]=Frame(tabs, height=tabheight, width=tabwidth)
    Tabs_Frames[t].pack(fill='both', expand=True, anchor=NW)


tabs.add(Tabs_Frames["Tab_Documents"], text="Documents")
tabs.add(Tabs_Frames["Tab_Canonicizers"], text="Canonicizers")
tabs.add(Tabs_Frames["Tab_EventDrivers"], text="Event Drivers")
tabs.add(Tabs_Frames["Tab_EventCulling"], text="Event Culling")
tabs.add(Tabs_Frames["Tab_AnalysisMethods"], text="Analysis Methods")
tabs.add(Tabs_Frames["Tab_ReviewProcess"], text="Review & Process")
#above is the tabs framework


#BELOW ARE CONFIGS FOR EACH TAB

#Note: the review & process tab is set-up first instead of last.

#####REVIEW & PROCESS TAB
#basic frames structure
Tab_ReviewProcess_Canonicizers=Frame(Tabs_Frames["Tab_ReviewProcess"])
Tab_ReviewProcess_Canonicizers.grid(row=0, column=0, columnspan=3, sticky="wens", padx=10, pady=10)

Tab_ReviewProcess_EventDrivers=Frame(Tabs_Frames["Tab_ReviewProcess"])
Tab_ReviewProcess_EventDrivers.grid(row=1, column=0, sticky="wens", padx=10, pady=10)

Tab_ReviewProcess_EventCulling=Frame(Tabs_Frames["Tab_ReviewProcess"])
Tab_ReviewProcess_EventCulling.grid(row=1, column=1, sticky="wens", padx=10, pady=10)

Tab_ReviewProcess_AnalysisMethods=Frame(Tabs_Frames["Tab_ReviewProcess"])
Tab_ReviewProcess_AnalysisMethods.grid(row=1, column=2, sticky="wens", padx=10, pady=10)

for n in range(3):
    Tabs_Frames["Tab_ReviewProcess"].columnconfigure(n, weight=1)
for n in range(2):
    Tabs_Frames["Tab_ReviewProcess"].rowconfigure(n, weight=1)

#RP = ReviewProcess
#note: the buttons below (that redirect to corresponding tabs) have hard-coded tab numbers
Tab_RP_Canonicizers_Button=Button(Tab_ReviewProcess_Canonicizers, text="Canonicizers", font=("helvetica", 16), relief=FLAT,\
    command=lambda:switch_tabs(tabs, "choose", 1), activeforeground="#333333")
Tab_RP_Canonicizers_Button.pack(anchor="n")

Tab_RP_Canonicizers_Listbox=Listbox(Tab_ReviewProcess_Canonicizers, selectbackground=accent_color_mid)
Tab_RP_Canonicizers_Listbox.pack(side=LEFT, expand=True, fill=BOTH)
Tab_RP_Canonicizers_Listbox_scrollbar=Scrollbar(Tab_ReviewProcess_Canonicizers, width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=Tab_RP_Canonicizers_Listbox.yview)
Tab_RP_Canonicizers_Listbox_scrollbar.pack(side=RIGHT, fill=BOTH)
Tab_RP_Canonicizers_Listbox.config(yscrollcommand=Tab_RP_Canonicizers_Listbox_scrollbar.set)

Tab_RP_EventDrivers_Button=Button(Tab_ReviewProcess_EventDrivers, text="Event Drivers", font=("helvetica", 16), relief=FLAT,\
    command=lambda:switch_tabs(tabs, "choose", 2))
Tab_RP_EventDrivers_Button.pack(anchor="n")

Tab_RP_EventDrivers_Listbox=Listbox(Tab_ReviewProcess_EventDrivers, selectbackground=accent_color_mid)
Tab_RP_EventDrivers_Listbox.pack(side=LEFT, expand=True, fill=BOTH)
Tab_RP_EventDrivers_Listbox_scrollbar=Scrollbar(Tab_ReviewProcess_EventDrivers, width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=Tab_RP_EventDrivers_Listbox.yview)
Tab_RP_EventDrivers_Listbox_scrollbar.pack(side=RIGHT, fill=BOTH)
Tab_RP_EventDrivers_Listbox.config(yscrollcommand=Tab_RP_EventDrivers_Listbox_scrollbar.set)
Tab_RP_EventCulling_Button=Button(Tab_ReviewProcess_EventCulling, text="Event Culling", font=("helvetica", 16), relief=FLAT,\
    command=lambda:switch_tabs(tabs, "choose", 3))
Tab_RP_EventCulling_Button.pack(anchor="n")

Tab_RP_EventCulling_Listbox=Listbox(Tab_ReviewProcess_EventCulling, selectbackground=accent_color_mid)
Tab_RP_EventCulling_Listbox.pack(side=LEFT, expand=True, fill=BOTH)
Tab_RP_EventCulling_Listbox_scrollbar=Scrollbar(Tab_ReviewProcess_EventCulling, width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=Tab_RP_EventCulling_Listbox.yview)
Tab_RP_EventCulling_Listbox_scrollbar.pack(side=RIGHT, fill=BOTH)
Tab_RP_EventCulling_Listbox.config(yscrollcommand=Tab_RP_EventCulling_Listbox_scrollbar.set)
Tab_RP_AnalysisMethods_Button=Button(Tab_ReviewProcess_AnalysisMethods, text="Analysis Methods", font=("helvetica", 16), relief=FLAT,\
    command=lambda:switch_tabs(tabs, "choose", 4))
Tab_RP_AnalysisMethods_Button.pack(anchor="n")

Tab_RP_AnalysisMethods_Listbox=Listbox(Tab_ReviewProcess_AnalysisMethods, selectbackground=accent_color_mid)
Tab_RP_AnalysisMethods_Listbox.pack(side=LEFT, expand=True, fill=BOTH)
Tab_RP_AnalysisMethods_Listbox_scrollbar=Scrollbar(Tab_ReviewProcess_AnalysisMethods, width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=Tab_RP_AnalysisMethods_Listbox.yview)
Tab_RP_AnalysisMethods_Listbox_scrollbar.pack(side=RIGHT, fill=BOTH)
Tab_RP_AnalysisMethods_Listbox.config(yscrollcommand=Tab_RP_AnalysisMethods_Listbox_scrollbar.set)
Tab_RP_Process_Button=Button(Tabs_Frames["Tab_ReviewProcess"], text="Process", width=25)

Tab_RP_Process_Button.config(\
    command=lambda lb=[Tab_RP_EventDrivers_Listbox, Tab_RP_AnalysisMethods_Listbox],\
        labels=[Tab_RP_EventDrivers_Button, Tab_RP_AnalysisMethods_Button],\
            button=Tab_RP_Process_Button:process("test", lb, labels, button, True))

Tab_RP_Process_Button.grid(row=2, column=0, columnspan=3, sticky="se", pady=5, padx=20)

Tab_RP_Process_Button.bind("<Map>", lambda event, a=[], lb=[Tab_RP_EventDrivers_Listbox, Tab_RP_AnalysisMethods_Listbox],\
    labels=[Tab_RP_EventDrivers_Button, Tab_RP_AnalysisMethods_Button],\
    button=Tab_RP_Process_Button:process(a, lb, labels, button))




############### DOCUMENTS TAB ########################################################################################################################

Tab_Documents_Language_label=Label(Tabs_Frames["Tab_Documents"], text="Language", font=("helvetica", 15), anchor='nw')
Tab_Documents_Language_label.grid(row=1, column=0, sticky='NW', pady=(10, 5))

for n in range(10):
    if n==5 or n==8:
        w=1
        Tabs_Frames["Tab_Documents"].columnconfigure(0, weight=1)

    else: w=0
    Tabs_Frames["Tab_Documents"].rowconfigure(n, weight=w)

#documents-language selection
analysisLanguage=StringVar()
analysisLanguage.set("English")
#may need a lookup function for the options below
analysisLanguageOptions=["Arabic (ISO-8859-6)", "Chinese (GB2123)", "English"]
Tab_Documents_language_dropdown=OptionMenu(Tabs_Frames["Tab_Documents"], analysisLanguage, *analysisLanguageOptions)
Tab_Documents_language_dropdown['anchor']='nw'
Tab_Documents_language_dropdown.grid(row=2, column=0, sticky='NW')



#documents-unknown authors
Tab_Documents_UnknownAuthors_label=Label(Tabs_Frames["Tab_Documents"], text="Unknown Authors", font=("helvetica", 15), anchor='nw')
Tab_Documents_UnknownAuthors_label.grid(row=4, column=0, sticky="W", pady=(10, 5))


Tab_Documents_UnknownAuthors_Frame=Frame(Tabs_Frames["Tab_Documents"])
Tab_Documents_UnknownAuthors_Frame.grid(row=5, column=0, sticky="wnse")


Tab_Documents_UnknownAuthors_listbox=Listbox(Tab_Documents_UnknownAuthors_Frame, width="100", selectbackground=accent_color_mid)
Tab_Documents_UnknownAuthors_listscrollbar=Scrollbar(Tab_Documents_UnknownAuthors_Frame, width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid)
#loop below: to be removed
for values in testfeatures[:5]:
    Tab_Documents_UnknownAuthors_listbox.insert(END, values)


Tab_Documents_UnknownAuthors_listbox.config(yscrollcommand=Tab_Documents_UnknownAuthors_listscrollbar.set)
Tab_Documents_UnknownAuthors_listscrollbar.config(command=Tab_Documents_UnknownAuthors_listbox.yview)


Tab_Documents_UnknownAuthors_listbox.pack(side=LEFT, fill=BOTH, expand=True)
Tab_Documents_UnknownAuthors_listscrollbar.pack(side=RIGHT, fill=BOTH, padx=(0, 30))

Tab_Documents_doc_buttons=Frame(Tabs_Frames["Tab_Documents"])
Tab_Documents_doc_buttons.grid(row=6, column=0, sticky="W")
Tab_Documents_UnknownAuthors_AddDoc_Button=Button(Tab_Documents_doc_buttons, text="Add Document", width="16", activebackground=accent_color_light, bg=accent_color_mid, command=\
    lambda:addFile("Add a document to Unknown Authors", Tab_Documents_UnknownAuthors_listbox, False))
Tab_Documents_UnknownAuthors_RmvDoc_Button=Button(Tab_Documents_doc_buttons, text="Remove Document", width="16", activebackground=accent_color_light, bg=accent_color_mid, command=\
    lambda:select_features(None, [Tab_Documents_UnknownAuthors_listbox], Tab_Documents_UnknownAuthors_listbox.curselection(), "remove"))

Tab_Documents_UnknownAuthors_AddDoc_Button.grid(row=1, column=1, sticky="W")
Tab_Documents_UnknownAuthors_RmvDoc_Button.grid(row=1, column=2, sticky="W")

#documents-known authors
Tab_Documents_KnownAuthors_label=Label(Tabs_Frames["Tab_Documents"], text="Known Authors", font=("helvetica", 15), anchor='nw')
Tab_Documents_KnownAuthors_label.grid(row=7, column=0, sticky="W", pady=(10, 5))


Tab_Documents_KnownAuthors_Frame=Frame(Tabs_Frames["Tab_Documents"])
Tab_Documents_KnownAuthors_Frame.grid(row=8, column=0, sticky="wnse")


Tab_Documents_KnownAuthors_listbox=Listbox(Tab_Documents_KnownAuthors_Frame, width="100")
Tab_Documents_KnownAuthors_listscroller=Scrollbar(Tab_Documents_KnownAuthors_Frame, width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid)

Tab_Documents_KnownAuthors_listbox.config(yscrollcommand=Tab_Documents_KnownAuthors_listscroller.set)
Tab_Documents_KnownAuthors_listscroller.config(command=Tab_Documents_KnownAuthors_listbox.yview)


Tab_Documents_KnownAuthors_listbox.pack(side=LEFT, fill=BOTH, expand=True)
Tab_Documents_KnownAuthors_listscroller.pack(side=RIGHT, fill=BOTH, padx=(0, 30))

#These are known authors
Tab_Documents_knownauth_buttons=Frame(Tabs_Frames["Tab_Documents"])
Tab_Documents_knownauth_buttons.grid(row=9, column=0, sticky="W")
Tab_Documents_KnownAuthors_AddAuth_Button=Button(Tab_Documents_knownauth_buttons, text="Add Author", width="15", activebackground=accent_color_light, bg=accent_color_mid,\
    command=lambda:authorsList(Tab_Documents_KnownAuthors_listbox, 'add'))
Tab_Documents_KnownAuthors_EditAuth_Button=Button(Tab_Documents_knownauth_buttons, text="Edit Author", width="15", activebackground=accent_color_light, bg=accent_color_mid,\
    command=lambda:authorsList(Tab_Documents_KnownAuthors_listbox, 'edit'))
Tab_Documents_KnownAuthors_RmvAuth_Button=Button(Tab_Documents_knownauth_buttons, text="Remove Author", width="15", activebackground=accent_color_light, bg=accent_color_mid, command=\
    lambda:authorsList(Tab_Documents_KnownAuthors_listbox, "remove"))

Tab_Documents_KnownAuthors_AddAuth_Button.grid(row=1, column=1, sticky="W")
Tab_Documents_KnownAuthors_EditAuth_Button.grid(row=1, column=2, sticky="W")
Tab_Documents_KnownAuthors_RmvAuth_Button.grid(row=1, column=3, sticky="W")





# This function creates canonicizers, event drivers, event culling, and analysis methods tabs.
def create_feature_tab(tab_frame: Frame, available_content: list, parameters_content=None, **extra):
    """
    creates a tab of available-buttons-selected-description tab.
    tab_frame: the top-level frame in the notebook tab
    available_content: list of label texts for the available features to go in.
    button_functions: list of buttons in the middle frame
    selected_content: list of names of listboxes for the selected features to go in.
    parameters_content: governs how the parameters frame is displayed
    description_content: governs how the descriptions frame is displayed.
    """
    assert len(set(available_content))==len(available_content), "Bug: create_features_tab: available_content can't have repeated names."
    global scrollbar_width
    global testfeatures
    global testfeatures_parameters

    # Layer 0
    objects=dict() # objects in the frame
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.rowconfigure(0, weight=1)

    topheight=0.7
    bottomheight=1-topheight
    
    objects["top_frame"]=Frame(tab_frame)
    #objects["top_frame"].grid(row=0, column=0, sticky="nwes")
    objects["top_frame"].place(relx=0, rely=0, relwidth=1, relheight=topheight)

    # Layer 1: main frames
    objects["available_frame"]=Frame(objects["top_frame"])
    #objects["available_frame"].grid(row=0, column=0, sticky="nwes")
    objects["available_frame"].place(relx=0, rely=0, relwidth=0.3, relheight=1)

    objects["buttons_frame"]=Frame(objects["top_frame"])
    #objects["buttons_frame"].grid(row=0, column=1, sticky="nwes")
    objects["buttons_frame"].place(relx=0.3, rely=0, relwidth=0.1, relheight=1)

    objects["selected_frame"]=Frame(objects["top_frame"])
    #objects["selected_frame"].grid(row=0, column=2, sticky="nwes")
    objects["selected_frame"].place(relx=0.4, rely=0, relwidth=0.3, relheight=1)

    if parameters_content!=None:
        objects["parameters_frame"]=Frame(objects["top_frame"])
        objects["parameters_frame"].place(relx=0.7, rely=0, relwidth=0.3, relheight=1)

        #objects["parameters_frame"].grid(row=0, column=3, sticky="nwes")

    objects["description_frame"]=Frame(tab_frame)
    #objects["description_frame"].grid(row=1, column=0, columnspan=4, sticky="nwes")
    objects["description_frame"].place(relx=0, rely=topheight, relheight=bottomheight, relwidth=1)

    # Layer 2: objects in main frames
    counter=0
    objects["available_listboxes"]=[]
    # each entry in objects["available_listboxes"]:
    # [frame, label, listbox, scrollbar]
    objects["available_frame"].columnconfigure(0, weight=1)

    for name in available_content:
        # "Available" listboxes
        objects["available_listboxes"].append([Frame(objects["available_frame"])])
        objects["available_listboxes"][-1][0].grid(row=counter, column=0, sticky="swen")

        objects["available_frame"].rowconfigure(counter, weight=1)

        objects["available_listboxes"][-1].append(Label(objects["available_listboxes"][-1][0], text=name, font=("Helvetica", 15)))
        objects["available_listboxes"][-1][1].pack(pady=(10, 5), side=TOP, anchor=NW)

        objects["available_listboxes"][-1].append(Listbox(objects["available_listboxes"][-1][0], selectbackground=accent_color_mid))
        objects["available_listboxes"][-1][2].pack(expand=True, fill=BOTH, side=LEFT)

        objects["available_listboxes"][-1].append(Scrollbar(objects["available_listboxes"][-1][0], width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=objects["available_listboxes"][-1][2].yview))
        objects["available_listboxes"][-1][3].pack(side=RIGHT, fill=BOTH)
        objects["available_listboxes"][-1][2].config(yscrollcommand=objects["available_listboxes"][-1][3].set)

        counter+=1

    objects["selected_listboxes"]=[]
    objects["selected_listboxes"].append([Frame(objects["selected_frame"])])
    objects["selected_listboxes"][-1][0].pack(expand=True, fill=BOTH)

    objects["selected_listboxes"][-1].append(Label(objects["selected_listboxes"][-1][0], text="Selected", font=("Helvetica", 15)))
    objects["selected_listboxes"][-1][1].pack(pady=(10, 5), side=TOP, anchor=NW)

    objects["selected_listboxes"][-1].append(Listbox(objects["selected_listboxes"][-1][0], selectbackground=accent_color_mid))
    objects["selected_listboxes"][-1][2].pack(expand=True, fill=BOTH, side=LEFT)

    objects["selected_listboxes"][-1].append(Scrollbar(objects["selected_listboxes"][-1][0], width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=objects["selected_listboxes"][-1][2].yview))
    objects["selected_listboxes"][-1][3].pack(side=RIGHT, fill=BOTH)
    objects["selected_listboxes"][-1][2].config(yscrollcommand=objects["selected_listboxes"][-1][3].set)

    Label(objects["buttons_frame"], text="", height=2).pack() # empty label to create space above buttons
    counter=0
    if extra.get("extra_buttons")==None: pass
    elif extra.get("extra_buttons")=="Canonicizers":
        extra.get("canonicizers_format")
        extra.get("canonicizers_format").set("All")
        CanonicizerFormatOptions=["All", "Generic", "Doc", "PDF", "HTML"]
        objects["Canonicizers_format"]=OptionMenu(objects["buttons_frame"], extra.get("canonicizers_format"), *CanonicizerFormatOptions)
        objects["Canonicizers_format"].pack(anchor=W)
        counter=1
    

    RP_listbox=extra.get("RP_listbox") # this is the listbox in the "Review and process" page to update when user adds a feature in previous pages.

    
    objects["buttons_add"]=Button(objects["buttons_frame"], width="11", text="Add", anchor='s', activebackground=accent_color_light, bg=accent_color_mid,
        command=lambda:select_features(objects["available_listboxes"][0][2], [objects["selected_listboxes"][0][2], RP_listbox], objects["available_listboxes"][0][2].curselection(), "add"))
    objects["buttons_add"].pack(anchor=CENTER, fill=X)

    objects["buttons_remove"]=Button(objects["buttons_frame"], width="11", text="Remove", anchor='s', activebackground=accent_color_light, bg=accent_color_mid,
        command=lambda:select_features(None, [objects["selected_listboxes"][0][2], RP_listbox], objects["selected_listboxes"][0][2].curselection(), "remove"))
    objects["buttons_remove"].pack(anchor=CENTER, fill=X)

    objects["buttons_clear"]=Button(objects["buttons_frame"], width="11", text="Clear", anchor='s', activebackground=accent_color_light, bg=accent_color_mid,
        command=lambda:select_features(None, [objects["selected_listboxes"][0][2], RP_listbox], objects["available_listboxes"][0][2].curselection(), "clear"))
    objects["buttons_clear"].pack(anchor=CENTER, fill=X)

    if parameters_content=="EventDrivers":
        displayed_parameters=extra.get("displayed_parameters")
        objects['parameters_label']=Label(objects["parameters_frame"], text="Parameters", font=("helvetica", 15), anchor=NW)
        objects['parameters_label'].pack(pady=(10, 5),anchor=W)

        objects['displayed_parameters_frame']=Frame(objects["parameters_frame"])
        objects['displayed_parameters_frame'].pack(padx=20, pady=20)

        objects["selected_listboxes"][-1][2].bind("<<ListboxSelect>>",\
            lambda event, frame=objects['displayed_parameters_frame'], lb=objects["selected_listboxes"][-1][2], dp=displayed_parameters:find_parameters(frame, lb, dp, None))
        objects["selected_listboxes"][-1][2].bind("<<Unmap>>",\
            lambda event, frame=objects['displayed_parameters_frame'], lb=objects["selected_listboxes"][-1][2], dp=displayed_parameters:find_parameters(frame, lb, dp))


    objects["description_label"]=Label(objects["description_frame"], text="Description", font=("helvetica", 15), anchor='nw')
    objects["description_label"].pack(anchor=NW, pady=(20, 5))
    objects["description_box"]=Text(objects["description_frame"], bd=5, relief="groove", bg=topwindow.cget("background"), state=DISABLED)
    objects["description_box"].pack(fill=BOTH, expand=True, side=LEFT)
    objects["description_box_scrollbar"]=Scrollbar(objects["description_frame"], width=scrollbar_width, activebackground=accent_color_light, bg=accent_color_mid, command=objects["description_box"].yview)
    objects["description_box"].config(yscrollcommand=objects["description_box_scrollbar"].set)
    objects["description_box_scrollbar"].pack(side=RIGHT, fill=BOTH)

    return objects

generated_widgets=dict()

CanonicizerFormat=StringVar()
generated_widgets['Canonicizers']=create_feature_tab(Tabs_Frames["Tab_Canonicizers"], ["Canonicizers"], extra_buttons="Canonicizers", canonicizers_format=CanonicizerFormat, RP_listbox=Tab_RP_Canonicizers_Listbox)
Tab_EventDrivers_Parameters_parameters_displayed=[]
generated_widgets['EventDrivers']=create_feature_tab(Tabs_Frames["Tab_EventDrivers"], ["Event Drivers"], "EventDrivers", displayed_parameters=Tab_EventDrivers_Parameters_parameters_displayed, RP_listbox=Tab_RP_EventDrivers_Listbox)
generated_widgets['EventCulling']=create_feature_tab(Tabs_Frames["Tab_EventCulling"], ["Event Culling"], RP_listbox=Tab_RP_EventCulling_Listbox)
generated_widgets['AnalysisMethods']=create_feature_tab(Tabs_Frames["Tab_AnalysisMethods"], ["Analysis Methods", "Distance Functions"], RP_listbox=Tab_RP_AnalysisMethods_Listbox)


# adding items to listboxes from the backendAPI.
#print(backendAPI.canonicizers)
for canonicizer in backendAPI.canonicizers:
    generated_widgets["Canonicizers"]["available_listboxes"][0][2].insert(END, canonicizer)
for driver in backendAPI.eventDrivers:
    generated_widgets["EventDrivers"]["available_listboxes"][0][2].insert(END, driver)
for distancefunc in backendAPI.distanceFunctions:
    generated_widgets["AnalysisMethods"]["available_listboxes"][1][2].insert(END, distancefunc)
for method in backendAPI.analysisMethods:
    generated_widgets["AnalysisMethods"]["available_listboxes"][0][2].insert(END, method)
#######

if debug>=2:
    _=0
    for j in generated_widgets:
        _+=len(j)
    print("size of 'generated_widgets' dict:", _)



#ABOVE ARE THE CONFIGS FOR EACH TAB

bottomframe=Frame(topwindow, height=150, width=570)
bottomframe.columnconfigure(0, weight=1)
bottomframe.rowconfigure(1, weight=1)
bottomframe.grid(pady=10, row=1, sticky='swen')

for c in range(6):
    bottomframe.columnconfigure(c, weight=10)

FinishButton=Button(bottomframe, text="Finish & Review", activebackground=accent_color_light, bg=accent_color_mid, command=lambda:switch_tabs(tabs, "choose", 5))#note: this button has a hard-coded tab number
PreviousButton=Button(bottomframe, text="<< Previous", activebackground=accent_color_light, bg=accent_color_mid, command=lambda:switch_tabs(tabs, "previous"))
NextButton=Button(bottomframe, text="Next >>", activebackground=accent_color_light, bg=accent_color_mid, command=lambda:switch_tabs(tabs, "next"))
Notes_Button=Button(bottomframe, text="Notes", activebackground=accent_color_light, bg=accent_color_mid, command=notepad)

Label(bottomframe).grid(row=0, column=0)
Label(bottomframe).grid(row=0, column=5)

PreviousButton.grid(row=0, column=1, sticky='swen')
NextButton.grid(row=0, column=2, sticky='swen')
Notes_Button.grid(row=0, column=3, sticky='swen')
FinishButton.grid(row=0, column=4, sticky='swen')

statusbar=Frame(topwindow, bd=1, relief=SUNKEN)
statusbar.grid(row=2, sticky="swe")

welcome_message="By David Berdik and Michael Fang. Version date: %s." %(versiondate)
statusbar_label=Label(statusbar, text=welcome_message, anchor=W)
statusbar_label.pack(anchor="e")
statusbar_label.after(3000, lambda:status_update("", statusbar_label['text']==welcome_message))

#starts app
topwindow.mainloop()
