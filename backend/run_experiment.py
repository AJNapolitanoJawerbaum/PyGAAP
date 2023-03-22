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

from traceback import format_exc

from datetime import datetime
from random import randint
from json import load as json_load


from backend.CSVIO import readDocument
from backend.Document import Document


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
		self.q = q
		self.default_mp = api.default_mp
		self.results_message = ""

	def run_pre_processing(self, **options):
		"""
		Run pre-processing on all documents:
		Canonicizers, event drivers, event cullers.
		"""
		# doc: the document passed in.
		# dump_queue: when multi-processing,
		# the shared queue to temporarily store the documents.
		verbose = options.get("verbose", False)
		if verbose and len(self.backend_API.modulesInUse["Canonicizers"]) > 0:
			print("Canonicizers processing ...")
		for c in self.backend_API.modulesInUse["Canonicizers"]:
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

		# if Document.canonicized is empty, default to original text
		no_canon = 0
		for doc in self.backend_API.documents:
			if doc.canonicized == "" or doc.canonicized is None:
				no_canon += 1
				doc.canonicized = doc.text
		if no_canon > 0 and len(self.backend_API.modulesInUse["Canonicizers"]) > 0:
			print("! %s/%s docs had no canonicized texts, defaulting to original texts."
				% (str(no_canon), str(len(self.backend_API.documents))))


		if verbose: print("Event drivers processing ...")
		succeeded_event_drivers = 0
		for e in self.backend_API.modulesInUse["EventDrivers"]:
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

		# check if any event drivers ran successfully. If all failed, stop.
		if succeeded_event_drivers == 0:
			this_error = "All event drivers failed."
			self.results_message += "\n" + this_error
			if verbose: print(this_error)
			exp_return = self.return_exp_results(
				results_text="", message=self.results_message, status=1,
			)
			return exp_return if self.return_results else 1

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


		if verbose and len(self.backend_API.modulesInUse["EventCulling"]) > 0:
			print("Event Cullers processing ...")
		for ec in self.backend_API.modulesInUse["EventCulling"]:
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

		self.results_message = ""
		status = 0

		# LOADING DOCUMENTS
		if self.pipe_here != None: self.pipe_here.send("Getting documents")
		print()
		if verbose:
			print("\nStarting experiment.\nGetting documents")

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

			for d in docs:
				try:
					d.text = readDocument(d.filepath)
				except:
					exp_return = self.return_exp_results(
						results_text="", message="Error reading file at:\n" + str(d.filepath), status=1,
					)
					return exp_return if self.return_results else 1
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
				self.results_message += "\nEmpty train set for these authors:\n" +\
					"\n".join(str(x) for x in empty_authors) + "\n"
				exp_return = self.return_exp_results(results_text="", message=self.results_message, status=1)
				return exp_return if self.return_results else 1
			elif sum([1 for x in known_docs if x.text.strip()==""]):
				exp_return = self.return_exp_results(results_text="", message="No documents in the train set", status=1)
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

		preproc_results = self.run_pre_processing(verbose=verbose)
		if preproc_results != 0:
			return preproc_results if self.return_results else 1

		if self.pipe_here != None: self.pipe_here.send(0)

		exp_params = dict()
		for mod_type in ["Canonicizers", "EventDrivers", "EventCulling"]:
			exp_params[mod_type] = []
			# each mod type list is a list because some are applied in order.
			for mod in self.backend_API.modulesInUse[mod_type]:
				exp_params[mod_type].append({"name": mod.__class__.displayName(),
					"params": {p:mod.__dict__[p] for p in mod.__dict__.keys() if not p.startswith("_")}}
				)

		# NUMBER CONVERSION: must take in all files in case there are author-based algorithms.
		results = [] # list of text-formatted results
		full_exp_dump = []# list of dict-formatted results
		nc_success_count = 0
		for nc in self.backend_API.modulesInUse["Embeddings"]:
			"""
			Only one embedder used for one analysis method
			This means for N embedders and M methods, there will be (N x M) analyses.
			"""
			nc._global_parameters = self.backend_API.global_parameters
			nc._default_multiprocessing = self.default_mp

			if self.pipe_here is not None:
				self.pipe_here.send("Running embedders")
				self.pipe_here.send(True)
			if verbose: print("Embedding ... running", nc.__class__.displayName())

			try:
				all_data = nc.convert(known_docs + unknown_docs, self.pipe_here)
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

			number_of_classifiers = len(self.backend_API.modulesInUse["AnalysisMethods"])
			if self.pipe_here is not None: self.pipe_here.send("Running analysis")

			am_success_count = 0
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

				am_df_pair[0].setDistanceFunction(am_df_pair[1])

				if self.pipe_here != None:
					self.pipe_here.send("Running - %s" % am_df_names_display)
					self.pipe_here.send(True)

				try:
        			# for each method: first train models on known docs
					am_df_pair[0].train(known_docs, known_docs_numbers_aggregate)
					# then for each unknown document, analyze and output results
					doc_results = am_df_pair[0].analyze(unknown_docs, unknown_docs_numbers_aggregate)
				except Exception as e:
					this_error = "\n" + "Analysis or distance function failed:\n" %\
						(am_df_pair[0].__class__.displayName(),
						am_df_pair[1].__class__.displayName(), str(e), format_exc())
					self.results_message += this_error
					if verbose: print(this_error)
					continue

				# by this line, both nc and am_df modules have successfully completed
				# "embeddings", "analysis methods", and "distance functions" are lists here for consistency
				# there should only be one of each of them.
				exp_params_out = deepcopy(exp_params)
				exp_params_out["Embeddings"] = [{
					"name": nc.__class__.displayName(),
					"params": {p:mod.__dict__[p] for p in mod.__dict__.keys() if not p.startswith("_")}
				}]
				exp_params_out["AnalysisMethods"] = [{
					"name": am_df_pair[0].__class__.displayName(),
					"params": {p:mod.__dict__[p] for p in mod.__dict__.keys() if not p.startswith("_")}
				}]
				exp_params_out["DistanceFunctions"] = [{
					"name": am_df_pair[1].__class__.displayName() if am_df_pair[1] != "NA" else "NA",
					"params": {p:mod.__dict__[p] for p in mod.__dict__.keys() if not p.startswith("_")}
						if am_df_pair[1] != "NA" else "NA"
				}]

				full_exp_dump.append({
					"modules": exp_params_out, "doc_results": {
						unknown_docs[i].filepath:doc_results[i] for i in range(len(unknown_docs))
					}
				})

				for d_index in range(len(unknown_docs)):
					formatted_results = \
						self.backend_API.prettyFormatResults(
							nc.__class__.displayName(),
							self.module_names["AnalysisMethods"][am_df_index],
							self.module_names["DistanceFunctions"][am_df_index],
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
			full_exp_dump=full_exp_dump,
			exp_time=str(datetime.now())
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
			"full_exp_dump": kwa.get("full_exp_dump", {}),
			"exp_time": kwa.get("exp_time", str(hex(randint(0, 10000000)))[2:])
		}
		if self.pipe_here != None: self.pipe_here.send(-1)
		if self.q != None:
			self.q.put(experiment_return)
			return
		if self.return_results:
			return experiment_return
