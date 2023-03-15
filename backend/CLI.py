import argparse, os, sys

from backend.CSVIO import *
from backend.Document import Document
from pathlib import Path
from time import time
from backend import run_experiment
from util.MultiprocessLoading import receive_info_text
from multiprocessing import Queue

def setParams(module_object, params_list: list, mod_name=""):
	for param in params_list:
		param_name = param.split(":")[0]
		param_value = param.split(":")[1]
		if type(param_value) != bool:
			try: # to identify numbers
				param_value = float(param_value)
				# if value is a number, try converting to a number.
				if abs(int(param_value) - param_value) < 0.0000001:
					param_value = int(param_value)
			except ValueError:
				pass
		validate = module_object.validate_parameter(param_name, param_value)
		if type(validate) == str or validate is False:
			raise AttributeError("Parameter validation failed for %s. Validator returned:\n%s" % (mod_name, validate))
		setattr(module_object, param_name, param_value)
	return

def cliMain():
	'''Main function for the PyGAAP CLI'''
	# this import is moved here (inside CLI function) to delay loading the API
	# i.e. let the CLI or GUI load the API instead of it being immediately loaded,
	# because it may take a long time to load depending on the modules,
	# and to also make the splash screen of the GUI work.
	# The GUI splash screen appears while API is loading so the app doesn't appear unresponsive.
	args = _parse_args()

	print("starting experiment(s)")
	# If a CSV file has been specified, process it.
	if args.experimentengine:
		from backend.API import API
		api = API([])
		# Get a list of experiments in the CSV.
		expCsvPath = args.experimentengine[0]
		experiments = readExperimentCSV(expCsvPath)
		
		# Process each experiment entry in the CSV.
		for exp in experiments:
			exp_name = exp[0]
			for mod_type in api.modulesInUse:
				api.modulesInUse[mod_type] = []
			api.documents = []
			# Get a list of entries in the specified corpus CSV.
			corpusEntries = readCorpusCSV(findCorpusCSVPath(exp[-1]))
			api.documents = []
			for doc in corpusEntries:
				api.documents.append(Document(
					doc[0], doc[2], readDocument(doc[1]), doc[1]
				))

			# now check for file format: whether PyGAAP exp csv or JGAAP exp csv
			if len(exp) == 8 or len(exp) == 9:
				# PyGAAP format
				canonicizers = exp[1].split('&')
				eventDrivers = exp[2].split('&')
				eventCulling = exp[3].split('&')
				embeddings = [exp[4]]
				if '&' in embeddings:
					raise ValueError("There can only be 1 embedder per experiment")
				analysisMethods = [exp[5]]
				if '&' in analysisMethods:
					raise ValueError("There can only be 1 analysis method per experiment")
				distanceFunctions = [exp[6]]
				if '&' in distanceFunctions:
					raise ValueError("There can only be 1 distance function per experiment")


			elif len(exp) == 6 or len(exp) == 7:
				# JGAAP format
				api.modulesInUse["Embeddings"] = [api.embeddings["Frequency"]()]
				canonicizers = exp[1].split('&')
				eventDrivers = exp[2].split('&')
				eventCulling = []
				analysisMethods = [exp[3]]
				distanceFunctions = [exp[4]]

			canonicizers = [x for x in canonicizers if x != ""]
			eventCulling = [x for x in eventCulling if x != ""]

			# now set the parameters
			for can in canonicizers:
				params = can.split("|")
				cc = params[0]
				mod = api.canonicizers[cc]()
				api.modulesInUse["Canonicizers"].append(mod)
				if len(params) > 1: 
					params = params[1:]
					setParams(mod, params, cc)

			for edr in eventDrivers:
				params = edr.split("|")
				ed = params[0]
				mod = api.eventDrivers[ed]()
				api.modulesInUse["EventDrivers"].append(mod)
				if len(params) > 1: 
					params = params[1:]
					setParams(mod, params, ed)

			for ecl in eventCulling:
				params = ecl.split("|")
				ec = params[0]
				mod = api.eventCulling[ec]()
				api.modulesInUse["EventCulling"].append(mod)
				if len(params) > 1: 
					params = params[1:]
					setParams(mod, params, ec)

			if len(exp) == 8 or len(exp) == 9:
				nmc = embeddings[0]
				params = nmc.split("|")
				nc = params[0]
				mod = api.embeddings[nc]()
				api.modulesInUse["Embeddings"].append(mod)
				if len(params) > 1:
					params = params[1:]
					setParams(mod, params, nc)

			anm = analysisMethods[0]
			params = anm.split("|")
			am = params[0]
			mod = api.analysisMethods[am]()
			api.modulesInUse["AnalysisMethods"].append(mod)
			if len(params) > 1:
				params = params[1:]
				setParams(mod, params, am)

			if mod._NoDistanceFunction_:
				api.modulesInUse["DistanceFunctions"].append("NA")
				if distanceFunctions != [""]:
					print("CLI: Warning:", mod.__class__.displayName(),
					"does not accept a distance function but one is specified. It will be ignored."
				)
			else:
				dis = distanceFunctions[0]
				params = dis.split("|")
				df = params[0]
				mod = api.distanceFunctions[df]()
				api.modulesInUse["DistanceFunctions"].append(mod)
				if len(params) > 1:
					params = params[1:]
					setParams(mod, params, df)

			experiment_runner = run_experiment.Experiment(api)
			exp_return = experiment_runner.run_experiment(skip_loading_docs=True, return_results=True)

			# Create the directories that the results will be stored in.
			outPath = os.path.join(Path.cwd(), "tmp",
				'&'.join(canonicizers).replace('|', '_').replace(':', '_'),
				'&'.join(eventDrivers).replace('|', '_').replace(':', '_'),
				analysisMethods[0].replace('|', '_').replace(':', '_')
				+ '-' + distanceFunctions[0].replace('|', '_').replace(':', '_'))
			if not os.path.exists(outPath):
				os.makedirs(outPath)
			out_filepath = os.path.join(outPath, (exp_name + str(int(time()))) + ".txt")
			print(out_filepath)
			expFile=open(out_filepath, 'w')
			expFile.write(exp_return["results_text"])
			expFile.close()
	print("Finished")

def _parse_args(empty=False):
	"""Parse command line arguments"""
	parser = argparse.ArgumentParser(description='Welcome to PyGAAP\u2014the Python Graphical Authorship Attribution Program')
	parser.add_argument('-ee', '--experimentengine', metavar='csv-file', nargs=1, help="Specifies a CSV file for batch processing multiple experiments at once.")
	# If no arguments specified, print help and completely exit.
	if empty:
		parser.print_help()
		sys.exit(1)
	
	# Return parsed arguments.
	return parser.parse_args()