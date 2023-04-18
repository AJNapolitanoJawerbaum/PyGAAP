# PyGAAP is the Python port of JGAAP,
# Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
#
# See PyGAAP_developer_manual.md for a guide to the structure of the GUI
# and how to add new modules.
# @ author: Michael Fang


from tkinter import Tk, Label, Toplevel, Text, Scrollbar, Button
from tkinter.ttk import Progressbar
from datetime import datetime

poll_frequency = 1

def receive_info_text(pipe, **options):
	if not pipe.poll():
		return
	info = pipe.recv()
	return info

def receive_info(
		pipe_connection,
		tkinter_user,
		**options,
		):
	# this runs in the same process as the GUI
	if not tkinter_user.winfo_exists():
		return 0

	text_label = options.get("text_label")
	progressbar = options.get("progressbar")

	end_run = options.get("end_run")
	# run this when the process ends (type function)
	if end_run != None:
		end_run_args = options.get("end_run_args")
		end_run_kwargs = options.get("end_run_kwargs")

	if not pipe_connection.poll():
		# if nothing heard from pipe, listen again later.
		options.get("after_user", tkinter_user).after(poll_frequency, lambda
			p=pipe_connection,
			u=tkinter_user,
			o=options:
				receive_info(p, u, **o)
		)
	else:
		# something received.
		info = pipe_connection.recv()
		if info == -1:
			pipe_connection.close()
			tkinter_user.destroy()
			if end_run != None:
				end_run(*end_run_args, **end_run_kwargs)
			return 0
		else:
			options.get("after_user", tkinter_user).after(poll_frequency, lambda
				p=pipe_connection,
				u=tkinter_user,
				o=options:
					receive_info(p, u, **o)
			)
			if type(info) == str:
				text_label.configure(text=info)
			elif type(info) == float or type(info) == int:
				progressbar["mode"] = "determinate"
				progressbar.stop()
				progressbar["value"] = info
			elif type(info) == bool:
				progressbar["mode"] = "indeterminate"
				progressbar.stop()
				if info: progressbar.start()
			return 0

def gui_abort_experiment(pipe, window, process, end_run, intermediate_queue):
	#pipe.close()
	# when the user presses the "abort" button.
	# Pull results from queue before killing process
	# (otherwise the queue may become unstable)
	intermediate_results = intermediate_queue.get(block=False, timeout=0.1)
	process.kill()
	window.destroy()
	end_run(abort=1, intermediate=intermediate_results)
	print("Experiment aborted")
	return
 

def process_window(geometry: str, mode: str, pto, **options):
	"""
	A process window,
	Can receive information through a pipe and adds a label to the window,
	or changes the label if one already exists.
	
	geometry	window size in tkinter format: e.g. "300x130" (as a string)
	pto			pipe connection, sending or receiving end.
	"""
	# this runs in the same process as the GUI
	progressbar_length = options.get("progressbar_length", 100)
	starting_text = options.get("starting_text", "")
	window_title = options.get("window_title", "Processing")
	if mode != "indetermintate" and mode != "determinate": mode = "indeterminate"

	end_run = options.get("end_run")
	end_run_args = options.get("end_run_args", [])
	end_run_kwargs = options.get("end_run_kwargs", dict())

	window = Toplevel()
	window.geometry(geometry)
	window.title(window_title)
	Label(window, text="Running experiment").pack(pady=(30,5))
	text_label = Label(window, text=starting_text)
	text_label.pack()
	progress = Progressbar(window, mode=mode, length=progressbar_length)
	progress.pack(padx=100, pady=(5,30))

	exp_process = options.get("exp_process")
	if exp_process is not None:
		abort_button = Button(window, text="Abort",
			command=lambda c=pto, w=window, p=exp_process, e=end_run,
			pq=options.get("intermediate"):
			gui_abort_experiment(c, w, p, e, pq))
		abort_button.pack(pady=10)

	receive_info(pto, window, text_label=text_label, progressbar=progress,
		end_run=end_run, end_run_args=end_run_args, end_run_kwargs=end_run_kwargs)

	if mode == "indeterminate": progress.start()
	return window


def splash(pto):
	"""Same as process_window(), only without the geometry."""
	# runs in a different process from GUI.
	loading_window = Tk()
	loading_window.geometry("400x200")
	loading_window.title("Loading")
	#loading_window.attributes('-type', 'splash')
	Label(loading_window, text="Starting PyGAAP").pack(pady=(30,5))
	text_label = Label(loading_window, text="")
	text_label.pack()
	progress = Progressbar(loading_window, mode="indeterminate", length=100)
	progress.pack(padx=100, pady=(5,30))

	receive_info(pto, loading_window, text_label=text_label, progressbar=progress)

	progress.start()
	loading_window.mainloop()
	return
