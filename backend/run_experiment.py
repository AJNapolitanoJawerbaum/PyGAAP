# PyGAAP is the Python port of JGAAP,
# Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
#
# See PyGAAP_developer_manual.md for a guide to the structure of the GUI
# and how to add new modules.
# @ author: Michael Fang


from multiprocessing import Process, Queue, Pipe, Pool	
from copy import deepcopy
from copy import copy as shallowcopy

import datetime
from json import load as json_load


from backend.CSVIO import readDocument
from backend.Document import Document


class Experiment:
	
	"""An experiment class to be invoked by either the GUI or the CLI."""

	backend_API = None
	module_names: dict = {}

	def __init__(self, api, module_names: dict, pipe_here=None, q:Queue=None, **options):
		"""
		Copies API in a different process (GUI)
		receives an end of a pipe to send info back to main process.
		"""
		self.gui_params = json_load(f:=open("./backend/GUI/gui_params.json", "r"))
		f.close()
		self.backend_API = shallowcopy(api)
		self.pipe_here = pipe_here
		self.module_names = module_names
		#self.dpi_setting = options.get("dpi")
		self.q = q
		self.default_mp = api.default_mp

	def run_pre_processing(self, **options):
		"""
		Run pre-processing on all documents:
		Canonicizers, event drivers, event cullers.
		"""
		# doc: the document passed in.
		# dump_queue: when multi-processing,
		# the shared queue to temporarily store the documents.
		print("Default multiprocessing:", self.default_mp)
		verbose = options.get("verbose", False)
		if verbose and len(self.backend_API.modulesInUse["Canonicizers"]) > 0:
			print("Canonicizers processing ...")
		for c in self.backend_API.modulesInUse["Canonicizers"]:
			if verbose: print("Running", c.__class__.displayName())
			if self.pipe_here is not None:
				self.pipe_here.send("Running canonicizers\n"+str(c.__class__.displayName()))
			c._default_multiprocessing = self.default_mp
			c._global_parameters = self.backend_API.global_parameters
			c.process(self.backend_API.documents, self.pipe_here)

		# if Document.canonicized is empty, default to original text
		no_canon = 0
		for doc in self.backend_API.documents:
			if doc.canonicized == "" or doc.canonicized is None:
				no_canon += 1
				doc.canonicized = doc.text
		if no_canon > 0:
			print("! %s/%s docs had no canonicized texts, defaulting to original texts. Expected if no canonicizers used."
				% (str(no_canon), str(len(self.backend_API.documents))))

		if verbose: print("Event drivers processing ...")
		for e in self.backend_API.modulesInUse["EventDrivers"]:
			if verbose: print("Running", e.__class__.displayName())
			if self.pipe_here is not None:
				self.pipe_here.send("Running event drivers\n"+str(e.__class__.displayName()))
			e._default_multiprocessing = self.default_mp
			e._global_parameters = self.backend_API.global_parameters
			e.process(self.backend_API.documents, self.pipe_here)

		if verbose and len(self.backend_API.modulesInUse["EventCulling"]) > 0:
			print("Event Cullers processing ...")
		for ec in self.backend_API.modulesInUse["EventCulling"]:
			ec._default_multiprocessing = self.default_mp
			if verbose: print("Running", ec.__class__.displayName())
			if self.pipe_here is not None:
				self.pipe_here.send("Running event culling\n"+str(ec.__class__.displayName()))
			ec._global_parameters = self.backend_API.global_parameters
			ec.process(self.backend_API.documents, self.pipe_here)
		if verbose: print()
		return

	def run_experiment(self, **options):

		"""
		Process all input files with the parameters in all tabs.
		input: unknown authors, known authors, all listboxes.
		"""
		self.return_results = options.get("return_results", False)
		verbose = options.get("verbose", False)

		results_message = ""
		status = 0

		# LOADING DOCUMENTS
		if self.pipe_here != None: self.pipe_here.send("Getting documents")
		if verbose: print("Getting documents")

		if not options.get("skip_loading_docs", False):

			# "loading docs" is skipped in CLI because
			# the CLI will load the docs.

			# gathering the documents for pre-processing
			# read documents here (at the last minute)
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

			for d in docs: d.text = readDocument(d.filepath)
			self.backend_API.documents = docs
		else:
			known_docs = [d for d in self.backend_API.documents if d.author != ""]
			unknown_docs = [d for d in self.backend_API.documents if d.author == ""]
			docs = known_docs + unknown_docs

		if verbose: print("checking params")
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
			empty_authors = {d.author for d in known_docs if d.text.strip()==""}
			if len(empty_authors) > 0:
				results_message += "Empty train set for these authors:\n" +\
					"\n".join(str(x) for x in empty_authors) + "\n"
				exp_return = self.return_exp_results(results_text="", message=results_message, status=1)
				return exp_return if self.return_results else 1
			elif sum([1 for x in known_docs if x.text.strip()==""]):
				exp_return = self.return_exp_results(results_text="", message="No documents in the train set", status=1)
				return exp_return if self.return_results else 1
		# check if any required mods are abscent
		if self.backend_API.modulesInUse["EventDrivers"] == [] or\
				self.backend_API.modulesInUse["NumberConverters"] == [] or\
				self.backend_API.modulesInUse["AnalysisMethods"] == []:
			exp_return = self.return_exp_results(results_text="",
				message="Missing Event drivers, number converters, or analysis methods", status=1)
			return exp_return if self.return_results else 1
		# check for analysis & distance functions mismatch.
		for i, am in enumerate(self.backend_API.modulesInUse["AnalysisMethods"]):
			if (am._NoDistanceFunction_ and self.backend_API.modulesInUse["DistanceFunctions"][i] != "NA") or\
				(not am._NoDistanceFunction_ and self.backend_API.modulesInUse["DistanceFunctions"][i] == "NA"):
				exp_return = self.return_exp_results(results_text="",
					message="Distance functions mismatch for %s." % am.displayName(),
				status=1)
				return exp_return if self.return_results else 1

		self.run_pre_processing(verbose=verbose)

		if self.pipe_here != None: self.pipe_here.send(0)

		# NUMBER CONVERSION: must take in all files in case there are author-based algorithms.
		results = []
		for nc in self.backend_API.modulesInUse["NumberConverters"]:
			"""
			Only one number converter used for one analysis method
			This means for N number converters and M methods, there will be (N x M) analyses.
			"""
			nc._global_parameters = self.backend_API.global_parameters
			nc._default_multiprocessing = self.default_mp

			if self.pipe_here is not None:
				self.pipe_here.send("Running number converters")
				self.pipe_here.send(True)
			if verbose: print("Embedding ... running", nc.__class__.displayName())
			all_data = nc.convert(known_docs + unknown_docs, self.pipe_here)
			known_docs_numbers_aggregate = all_data[:len(known_docs)]
			unknown_docs_numbers_aggregate = all_data[len(known_docs):]
			del all_data

			number_of_classifiers = len(self.backend_API.modulesInUse["AnalysisMethods"])
			if self.pipe_here is not None: self.pipe_here.send("Running analysis")
			for am_df_index in range(number_of_classifiers):
				if verbose:
					print("Classifying ... running",
						self.backend_API.modulesInUse["AnalysisMethods"][am_df_index].__class__.displayName())
				am_df_pair = (self.backend_API.modulesInUse["AnalysisMethods"][am_df_index],
							self.backend_API.modulesInUse["DistanceFunctions"][am_df_index])
				am_df_pair[0]._global_parameters = self.backend_API.global_parameters
				if am_df_pair[1] != "NA":
					am_df_pair[1]._global_parameters = self.backend_API.global_parameters

				am_df_names_display = [self.module_names["AnalysisMethods"][am_df_index],
											self.module_names["DistanceFunctions"][am_df_index]]
				if am_df_names_display[1] == "NA": am_df_names_display = am_df_names_display[0]
				else: am_df_names_display = am_df_names_display[0] + ', ' + am_df_names_display[1]
				if self.pipe_here != None: self.pipe_here.send("Training - %s" % str(am_df_names_display))

				am_df_pair[0].setDistanceFunction(am_df_pair[1])
				
				# for each method: first train models on known docs
				am_df_pair[0].train(known_docs, known_docs_numbers_aggregate)
				# then for each unknown document, analyze and output results
				
				if self.pipe_here != None:
					self.pipe_here.send("Analyzing - %s" % am_df_names_display)
					self.pipe_here.send(True)

				doc_results = am_df_pair[0].analyze(unknown_docs, unknown_docs_numbers_aggregate)

				for d_index in range(len(unknown_docs)):

					formatted_results = \
						self.backend_API.prettyFormatResults(
							self.module_names["Canonicizers"],
							self.module_names["EventDrivers"],
							self.module_names["EventCulling"],
							self.module_names["NumberConverters"],
							self.module_names["AnalysisMethods"][am_df_index],
							self.module_names["DistanceFunctions"][am_df_index],
							unknown_docs[d_index],
							doc_results[d_index]
						)
					results.append(formatted_results)

		results_text = ""
		for r in results:
			results_text += str(r + "\n")

		# if self.pipe_here != None: self.pipe_here.send(-1)

		exp_return = self.return_exp_results(
			results_text=results_text,
			message=results_message,
			status=status,
		)
		print("Experiment done.")
		if self.return_results:
			return exp_return
		return
		

	def return_exp_results(self, **kwa):
		experiment_return = {
			"results_text": kwa.get("results_text", ""),
			"message": kwa.get("message", "No message provided."),
			"status": kwa.get("status", 1),
		}
		if self.pipe_here != None: self.pipe_here.send(-1)
		if self.q != None:
			self.q.put(experiment_return)
			return
		if self.return_results:
			return experiment_return
