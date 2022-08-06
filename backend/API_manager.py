from backend import API
from multiprocessing import Process, Queue, Pipe
from multiprocessing.connection import Connection
from backend.GUI import GUI_run_experiment



"""
This is a module to maintain compatibility with Windows.
It runs in the same process as the GUI, but starts another process
with the API by initializing API_process, and sends/receives signals.

When the experiment starts, it creates a copy of the API which
takes in all the module info and parameters through a pipe
instead of passing the modules and/or the API objects themselves because
they're not picklable.
"""


def manager_run_exp(api, pipe_mainproc: Connection, pipe_subproc: Connection,
		progress_report_there: Connection, mod_names, q):
	"""a static method that creates a process"""
	api_process = Process(target=API_process, args=(pipe_subproc, pipe_mainproc, progress_report_there, mod_names, q))
	api_process.start()


	pipe_mainproc.send(("known_authors", api.known_authors))
	pipe_mainproc.send(("unknown_docs", api.unknown_docs))
	pipe_mainproc.send(("global_parameters", api.global_parameters))
	pipe_mainproc.send("End docs and global params")

	for mod_type in mod_names:
		for mod_i in range(len(mod_names[mod_type])):
			mod_name = mod_names[mod_type][mod_i]
			mod = \
				api.modulesInUse[mod_type][mod_i]

			pipe_mainproc.send((mod_type, mod_name))
			if mod_name == "NA": continue
			else:
				for attribute in mod.__dict__:
					if attribute[0] == "_": continue
					pipe_mainproc.send((mod_name, attribute, mod.__dict__.get(attribute)))
			pipe_mainproc.send("End params")

	pipe_mainproc.send("End mods")
	pipe_mainproc.close()
	pipe_subproc.close()
	return




def API_process(pipe_subproc: Connection,
		pipe_mainproc: Connection,
		prog_report_pipe: Connection,
		mod_names: dict,
		results_queue):
	api = API.API("")
	# first eceive documents, and create modules
	pipe_subproc: Connection = pipe_subproc
	pipe_mainproc: Connection = pipe_mainproc
	while True:
		if not pipe_subproc.poll(): continue
		heard = pipe_subproc.recv()
		if heard == "End docs and global params": break
		setattr(api, heard[0], heard[1])
	while True:
		if not pipe_subproc.poll(): continue
		heard = pipe_subproc.recv()
		if heard == "End mods": break
		mod_type, mod_name = heard
		if mod_name == "NA":
			api.modulesInUse[mod_type].append("NA")
			continue
			
		mod_obj = api.moduleTypeDict[mod_type][mod_name]()
		api.modulesInUse[mod_type].append(mod_obj)

		heard = pipe_subproc.recv()
		while heard != "End params":
			mod_name2, mod_attribute, mod_attribute_value = heard
			assert mod_name2 == mod_name, \
				"Module name mismatch while communicating between processes. %s != %s" % (mod_name, mod_name2)
			setattr(mod_obj, mod_attribute, mod_attribute_value)
			heard = pipe_subproc.recv()
	exp = GUI_run_experiment.Experiment(api, mod_names, prog_report_pipe, results_queue)
	exp.run_experiment()

	return



