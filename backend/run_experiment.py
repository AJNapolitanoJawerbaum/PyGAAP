# PyGAAP is the Python port of JGAAP,
# Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
#
# See PyGAAP_developer_manual.md for a guide to the structure of the GUI
# and how to add new modules.
# @ author: Michael Fang


from multiprocessing import Process, Queue, Pipe, Pool
from multiprocessing.queues import Empty as queue_empty
from copy import deepcopy
from copy import copy as shallowcopy
import re

from traceback import format_exc

from datetime import datetime
from random import randint
from json import load as json_load
from os import mkdir, path as os_path

from backend.CSVIO import readDocument
from backend.Document import Document

from pickle import dump as pickle_dump

EXP_DEBUG = 0
DEBUG_DIR = "./tmp"

class Experiment:

	"""An experiment class to be invoked by either the GUI or the CLI."""

	backend_API = None
	module_names: dict = {}

	def __init__(self, api, pipe_here=None, q:Queue=None, **options):
		"""
		Copies API in a different process (GUI)
		receives an end of a pipe to send info back to main process.
		"""
		self.gui_params = None
		with open("./resources/gui_params.json", "r") as f:
			self.gui_params = json_load(f)
		self.backend_API = shallowcopy(api)
		self.pipe_here = pipe_here

		self.module_names = {mod_type:[(mod.__class__.displayName() if mod != "NA" else "NA")
			for mod in self.backend_API.modulesInUse[mod_type]]
			for mod_type in self.backend_API.modulesInUse}
		#self.dpi_setting = options.get("dpi")
		self.q: Queue = q
		self.default_mp = api.default_mp
		self.results_message = ""
		self.intermediate: Queue = options.get("intermediate", None) # capacity 1

		self.full_exp_dump: list = [] # the complete exp parameters
		return

	def dump_intermediate(self):
		"""Dump pickle file if experiment is aborted"""
		if self.intermediate is None: return 0
		try:
			self.intermediate.get(block=False, timeout=0.01) # first clear the 1-element queue.
		except queue_empty: pass
		self.intermediate.put({"documents": self.backend_API.documents, "full_exp_dump": self.full_exp_dump})
		return 0

	def run_pre_processing(self, **options):
		"""
		Run pre-processing on all documents:
		Canonicizers, event drivers, event cullers.
		"""
		# doc: the document passed in.
		verbose = options.get("verbose", False)
		if verbose and len(self.backend_API.modulesInUse["Canonicizers"]) > 0:
			print("Canonicizers processing ...")
		# for d in self.backend_API.documents:
		# 	d.text = re.subn(re.compile("(?<!\r)\n"), "\r\n", d.text)[0]

		# RUN CANONICIZERS
		for i, c in enumerate(self.backend_API.modulesInUse["Canonicizers"]):
			if verbose: print("Running", c.__class__.displayName())
			if self.pipe_here is not None:
				self.pipe_here.send("Running canonicizers\n"+str(c.__class__.displayName()))
			c._default_multiprocessing = self.default_mp
			c._global_parameters = self.backend_API.global_parameters
			try:
				c.process(self.backend_API.documents, self.pipe_here)
			except Exception as error:
				# allow exp to continue if any or all canonicizers failed, but raise warning.
				this_error = "\nCanonicizer failed: %s\n%s\n%s\n" %\
					(c.__class__.displayName(), str(error), format_exc())
				self.results_message += this_error
				if verbose: print(this_error)

			for exp in self.full_exp_dump:
				exp["modules"]["Canonicizers"][i]["completed"] = 1
			self.dump_intermediate()

		if EXP_DEBUG == 2:
			with open("./tmp/1_api_canonicized", "wb") as api_dump:
				pickle_dump(self.backend_API.documents, api_dump)

		# if Document.canonicized is empty (no canonicizers), move original text to doc.canonicized
		no_canon = 0
		for doc in self.backend_API.documents:
			if doc.canonicized == "" or doc.canonicized is None:
				no_canon += 1
				doc.canonicized = doc.text
				doc.text = ""
		if no_canon > 0 and len(self.backend_API.modulesInUse["Canonicizers"]) > 0:
			print("! %s/%s docs had no canonicized texts, defaulting to original texts."
				% (str(no_canon), str(len(self.backend_API.documents))))

		# RUN EVENT DRIVERS
		if verbose: print("Event drivers processing ...")
		succeeded_event_drivers = 0
		for i, e in enumerate(self.backend_API.modulesInUse["EventDrivers"]):
			if verbose: print("Running", e.__class__.displayName())
			if self.pipe_here is not None:
				self.pipe_here.send("Running event drivers\n"+str(e.__class__.displayName()))
			e._default_multiprocessing = self.default_mp
			e._global_parameters = self.backend_API.global_parameters
			try:
				e.process(self.backend_API.documents, self.pipe_here)
				succeeded_event_drivers += 1
			except Exception as error:
				this_error = "\nEvent driver failed: %s\n%s\n%s\n" %\
					(e.__class__.displayName(), str(error), format_exc())
				self.results_message += this_error
				if verbose: print(this_error)

			for exp in self.full_exp_dump:
				exp["modules"]["EventDrivers"][i]["completed"] = 1
			self.dump_intermediate()

		# check if any event drivers ran successfully. If all failed, stop.
		if succeeded_event_drivers == 0:
			this_error = "All event drivers failed."
			self.results_message += "\n" + this_error
			if verbose: print(this_error)
			exp_return = self.return_exp_results(
				results_text="", message=self.results_message, status=1,
			)
			return exp_return if self.return_results else 1

		if EXP_DEBUG == 2:
			with open("./tmp/2_api_events_raw", "wb") as api_dump:
				pickle_dump(self.backend_API.documents, api_dump)

		# abort if any doc ends up having no events.
		empty_event_sets = [doc.title for doc in self.backend_API.documents if len(doc.eventSet)==0]
		if len(empty_event_sets) > 0:
			this_error = ("%s/%s docs had no event sets after event extraction."
				% (str(len(empty_event_sets)), str(len(self.backend_API.documents))))
			self.results_message += this_error
			exp_return = self.return_exp_results(
				results_text="", message=self.results_message, status=1,
			)
			return exp_return if self.return_results else 1

		# RUN EVENT FILTERING
		if verbose and len(self.backend_API.modulesInUse["EventCulling"]) > 0:
			print("Event Cullers processing ...")
		for i, ec in enumerate(self.backend_API.modulesInUse["EventCulling"]):
			ec._default_multiprocessing = self.default_mp
			if verbose: print("Running", ec.__class__.displayName())
			if self.pipe_here is not None:
				self.pipe_here.send("Running event culling\n"+str(ec.__class__.displayName()))
			ec._global_parameters = self.backend_API.global_parameters
			try:
				ec.process(self.backend_API.documents, self.pipe_here)
			except Exception as error:
				this_error = "\nEvent culler failed: %s\n%s\n%s\n" %\
					(ec.__class__.displayName(), str(error), format_exc())
				self.results_message += this_error
				if verbose: print(this_error)

			for exp in self.full_exp_dump:
				exp["modules"]["EventCulling"][i]["completed"] = 1
			self.dump_intermediate()

		if EXP_DEBUG == 2:
			with open("./tmp/3_api_event_filtered", "wb") as api_dump:
				pickle_dump(self.backend_API.documents, api_dump)

		# allow the exp to continue if any or all cullers failed, but raise warning.
		empty_event_sets = [doc for doc in self.backend_API.documents if len(doc.eventSet)==0]
		if len(empty_event_sets) > 0:
			this_error = "! %s/%s docs had no event sets after event culling:\n"\
				% (str(len(empty_event_sets)), str(len(self.backend_API.documents)))
			this_error += "\n".join([d.filepath for d in empty_event_sets]) + "\n"
			exp_return = self.return_exp_results(
				results_text="", message=self.results_message + this_error, status=1,
			)
			return exp_return if self.return_results else 1

		return 0

	def run_experiment(self, **options):

		"""
		Process all input files with the parameters in all tabs.
		input: unknown authors, known authors, all listboxes.
		"""
		self.return_results = options.get("return_results", False)
		verbose = options.get("verbose", False)

		self.hide_filepath = options.get("filepath", False)

		self.results_message = ""
		status = 0

		if EXP_DEBUG == 2 and not os_path.isdir(DEBUG_DIR):
			try: mkdir(DEBUG_DIR)
			except FileExistsError: raise FileExistsError("Expected debug directory at %s but it's not a directory."
				"Disable debug (EXP_DEBUG=0) or change DEBUG_DIR at ./backend/run_experiment.py.")

		exp_time = str(datetime.now())

		# LOADING DOCUMENTS
		if self.pipe_here != None: self.pipe_here.send("Getting documents")
		print()
		if verbose:
			print("\nStarting experiment.\nGetting documents")

		if not options.get("skip_loading_docs", False):
			# GUI
			# gathering the documents for pre-processing
			docs = []
			for author in self.backend_API.known_authors:
				for authorDoc in author[1]:
					docs.append(Document(author[0],
						authorDoc.split("/")[-1],
						"", authorDoc))

			# make copies for use in processing.
			# This is much faster than deepcopying after reading the files,
			# especially for long files.
			known_docs = shallowcopy(docs)
			docs += self.backend_API.unknown_docs
			unknown_docs = self.backend_API.unknown_docs
			self.backend_API.documents = docs
		else:
			# CLI
			# "loading docs" is skipped in CLI because
			# the CLI will load the docs.
			known_docs = [d for d in self.backend_API.documents if d.author != ""]
			unknown_docs = [d for d in self.backend_API.documents if d.author == ""]
			docs = known_docs + unknown_docs
			self.backend_API.documents = docs

		for d in self.backend_API.documents:
			try:
				# get the texts of the docs.
				d.read_self()
			except:
				exp_return = self.return_exp_results(
					results_text="", message="Error reading file at:\n" + str(d.filepath) + "\n" +
					format_exc(), status=1,
				)
				return exp_return if self.return_results else 1
			

		# api documents: known texts first followed by unknown texts.

		if verbose: print("checking params")
		# Checking params to make the API more independent from the front end
		# validate modules, documents:
		# check test set
		if len(unknown_docs) == 0:
			exp_return = self.return_exp_results(
				results_text="", message="No documents in the test set", status=1,
			)
			return exp_return if self.return_results else 1
		# check train set
		if len(known_docs) == 0:
			exp_return = self.return_exp_results(
				results_text="", message="No documents in the train set", status=1,
			)
			return exp_return if self.return_results else 1
		else:
			# train set: check if a class has no train files
			empty_files = [d.filepath for d in known_docs if d.text.strip()==""]
			if len(empty_files):
				self.results_message += "\nEmpty files in the training set:\n" +\
					"\n".join(str(x) for x in empty_files) + "\n"
				exp_return = self.return_exp_results(results_text="", message=self.results_message, status=1)
				return exp_return if self.return_results else 1
		# check if any required mods are abscent
		if self.backend_API.modulesInUse["EventDrivers"] == [] or\
				self.backend_API.modulesInUse["Embeddings"] == [] or\
				self.backend_API.modulesInUse["AnalysisMethods"] == []:
			exp_return = self.return_exp_results(results_text="",
				message="Missing one or more of Event drivers, embedders, or analysis methods", status=1)
			return exp_return if self.return_results else 1
		# check for analysis & distance functions mismatch.
		for i, am in enumerate(self.backend_API.modulesInUse["AnalysisMethods"]):
			if (am._NoDistanceFunction_ and self.backend_API.modulesInUse["DistanceFunctions"][i] != "NA") or\
				(not am._NoDistanceFunction_ and self.backend_API.modulesInUse["DistanceFunctions"][i] == "NA"):
				exp_return = self.return_exp_results(results_text="",
					message='Distance functions mismatch for %s. Distance function: "%s"' %
					(am.displayName(), self.backend_API.modulesInUse["DistanceFunctions"][i]),
				status=1)
				return exp_return if self.return_results else 1

		# experiment docs, mods, and parameters validated at this point.
		# log parameters to full_exp_dump

		self.full_exp_dump = [] # list of dict-formatted results. Each element in the list is an experiment.
		exp_params = dict()
		for mod_type in ["Canonicizers", "EventDrivers", "EventCulling"]:
			exp_params[mod_type] = []
			# each mod type list is a list because some are applied in order.
			for mod in self.backend_API.modulesInUse[mod_type]:
				exp_params[mod_type].append({
						"name": mod.__class__.displayName(),
						"params": {p:mod.__dict__[p] for p in mod.__dict__.keys() if not p.startswith("_")},
						"completed": 0
					}
				)

		for nc in self.backend_API.modulesInUse["Embeddings"]:
			for am_i, am in enumerate(self.backend_API.modulesInUse["AnalysisMethods"]):
				df = self.backend_API.modulesInUse["DistanceFunctions"][am_i]
				exp_params_out = deepcopy(exp_params)
				exp_params_out["Embeddings"] = [{
					"name": nc.__class__.displayName(),
					"params": {p:nc.__dict__[p] for p in nc.__dict__.keys() if not p.startswith("_")},
					"completed": 0
				}]
				exp_params_out["AnalysisMethods"] = [{
					"name": am.__class__.displayName(),
					"params": {p:am.__dict__[p] for p in am.__dict__.keys() if not p.startswith("_")},
					"completed": 0
				}]
				exp_params_out["DistanceFunctions"] = [{
					"name": df.__class__.displayName() if df != "NA" else "NA",
					"params": {p:df.__dict__[p] for p in df.__dict__.keys() if not p.startswith("_")}
						if df != "NA" else "NA",
				}]

				self.full_exp_dump.append({
					"modules": exp_params_out,
					"exp_time": exp_time,
					"success": 0,
					"documents": [
						{"author": doc.author, "title": doc.title,
						"filepath": "[hidden]" if self.hide_filepath else doc.filepath}
						for doc in self.backend_API.documents
					],
					"global_parameters": self.backend_API.global_parameters,
					"doc_results": None
				})

		# begin experiment with pre-processing to feature extraction

		preproc_results = self.run_pre_processing(verbose=verbose)
		if preproc_results != 0:
			return preproc_results if self.return_results else 1

		if self.pipe_here != None: self.pipe_here.send(0)

		exp_dump_index = 0	

		# EMBEDDING: must take in all files in case there are author-based algorithms.
		results = [] # list of results represented as strings
		nc_success_count = 0
		for nc_i, nc in enumerate(self.backend_API.modulesInUse["Embeddings"]):
			"""
			Only one embedder used for one analysis method
			This means for N embedders and M classifiers, there will be (N x M) analyses.
			"""
			nc._global_parameters = self.backend_API.global_parameters
			nc._default_multiprocessing = self.default_mp

			if self.pipe_here is not None:
				self.pipe_here.send("Running embedders")
				self.pipe_here.send(True)
			if verbose: print("Embedding ... running", nc.__class__.displayName())

			try:
				all_data = nc.process(known_docs + unknown_docs, self.pipe_here)
			except Exception as error:
				this_error = "\nembedder failed: %s\n%s\n%s\n" %\
					(nc.__class__.displayName(), str(error), format_exc())
				self.results_message += this_error
				if verbose: print(this_error)
				# if an NC failed, allow to continue because the next may work. But raise a warning.
				continue
			known_docs_numbers_aggregate = all_data[:len(known_docs)]
			unknown_docs_numbers_aggregate = all_data[len(known_docs):]
			del all_data

			if EXP_DEBUG == 2:
				with open("./tmp/4_api_embedded_%s" % nc.__class__.displayName().replace(" ", "_"), "wb") as api_dump:
					pickle_dump(self.backend_API.documents, api_dump)

			self.full_exp_dump[exp_dump_index]["modules"]["Embeddings"][0]["completed"] = 1
			self.dump_intermediate()

			if self.pipe_here is not None: self.pipe_here.send("Running analysis")

			# RUN CLASSIFIERS
			am_success_count = 0
			for am_df_i, am in enumerate(self.backend_API.modulesInUse["AnalysisMethods"]):
				df = self.backend_API.modulesInUse["DistanceFunctions"][am_df_i]
				if verbose:
					print("Classifying ... running", am.__class__.displayName())
				am_df_pair = (am, df)
				am_df_pair[0]._global_parameters = self.backend_API.global_parameters
				if am_df_pair[1] != "NA":
					am_df_pair[1]._global_parameters = self.backend_API.global_parameters

				am_df_names_display = [self.module_names["AnalysisMethods"][am_df_i],
											self.module_names["DistanceFunctions"][am_df_i]]
				if am_df_names_display[1] == "NA": am_df_names_display = am_df_names_display[0]
				else: am_df_names_display = am_df_names_display[0] + ', ' + am_df_names_display[1]

				am_df_pair[0].setDistanceFunction(am_df_pair[1])

				if self.pipe_here != None:
					self.pipe_here.send("Running - %s" % am_df_names_display)
					self.pipe_here.send(True)

				try:
					# am_df_pair[0].train(known_docs, known_docs_numbers_aggregate)
					# doc_results = am_df_pair[0].analyze(unknown_docs, unknown_docs_numbers_aggregate)
					doc_results = am_df_pair[0].process(docs, self.pipe_here,
						known_numbers=known_docs_numbers_aggregate, unknown_numbers=unknown_docs_numbers_aggregate)
				except Exception as e:
					this_error = "\n" + "Analysis or distance function failed:\n%s, %s\n\n%s\n\n%s" %\
						(am_df_pair[0].__class__.displayName(),
						am_df_pair[1].__class__.displayName(), str(e), format_exc())
					self.results_message += this_error
					if verbose: print(this_error)
					continue

				if EXP_DEBUG == 2:
					with open(
								"./tmp/5_api_analyzed_%s_%s" %
								(am_df_pair[0].__class__.displayName().replace(" ", "_"),
								am_df_pair[1].__class__.displayName().replace(" ", "_")), "wb"
							) as api_dump:
						pickle_dump(self.backend_API.documents, api_dump)

				self.full_exp_dump[exp_dump_index]["modules"]["AnalysisMethods"][0]["completed"] = 1
				self.dump_intermediate()

				# by this line, both nc and am_df modules have successfully completed
				# "embeddings", "analysis methods", and "distance functions" are lists here for consistency
				# there should only be one of each of them.

				self.full_exp_dump[exp_dump_index]["doc_results"] = {
					unknown_docs[x].filepath:doc_results[x] for x in range(len(unknown_docs))
				}
				self.full_exp_dump[exp_dump_index]["success"] = 1
				exp_dump_index += 1

				for d_index in range(len(unknown_docs)):
					formatted_results = \
						self.backend_API.prettyFormatResults(
							nc.__class__.displayName(),
							self.module_names["AnalysisMethods"][am_df_i],
							self.module_names["DistanceFunctions"][am_df_i],
							unknown_docs[d_index],
							doc_results[d_index]
						)
					results.append(formatted_results)
				am_success_count += 1

			if am_success_count <= 0:
				# if all analysis methods failed for one type of embedding,
				# allow to continue, because some analyses may work for the next
				# embedding method.
				continue
			else:
				nc_success_count += 1

		if nc_success_count <= 0:
			# if all analysis failed for all NCs, abort.
			exp_return = self.return_exp_results(results_text="",
				message=self.results_message, status=1)
			return exp_return if self.return_results else 1


		results_text = ""
		for r in results:
			results_text += str(r + "\n")

		# if self.pipe_here != None: self.pipe_here.send(-1)

		exp_return = self.return_exp_results(
			results_text=results_text,
			message=self.results_message,
			status=status,
			full_exp_dump=self.full_exp_dump,
			exp_time=exp_time
		)
		print("Experiment done.")
		if self.return_results:
			return exp_return
		return 0
		

	def return_exp_results(self, **kwa):
		experiment_return = {
			"results_text": kwa.get("results_text", ""),
			"message": kwa.get("message", "No message provided."),
			"status": kwa.get("status", 1),
			"full_exp_dump": kwa.get("full_exp_dump", {}),
			"exp_time": kwa.get("exp_time", str(hex(randint(0, 10000000)))[2:])
		}
		if self.pipe_here != None: self.pipe_here.send(-1)
		if self.q != None:
			self.q.put(experiment_return)
			return
		if self.return_results:
			return experiment_return
