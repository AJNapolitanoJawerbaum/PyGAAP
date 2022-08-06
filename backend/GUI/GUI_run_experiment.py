# PyGAAP is the Python port of JGAAP,
# Java Graphical Authorship Attribution Program by Patrick Juola
# For JGAAP see https://evllabs.github.io/JGAAP/
#
# See PyGAAP_developer_manual.md for a guide to the structure of the GUI
# and how to add new modules.
# @ author: Michael Fang

# this is closely coupled with the main file ~/backend/GUI/GUI2.py.
# this file is separate from GUI2.py for readability only.


from multiprocessing import Process, Queue, Pipe, Pool	
from copy import deepcopy
from copy import copy as shallowcopy

import datetime
from json import load as json_load

#from backend import API


from backend.CSVIO import readDocument
from backend.Document import Document
#from generics.NumberConverter import NumberConverter


GUI_debug = 0

class Experiment:

	backend_API = None
	module_names: dict = {}

	def __init__(self, api, module_names: dict, pipe_here=None, q:Queue=None, **options):
		"""
		Copies API in a different process
		receives an end of a pipe to send info back to main process.
		"""
		self.gui_params = json_load(f:=open("./backend/GUI/gui_params.json", "r"))
		f.close()
		self.backend_API = shallowcopy(api)
		self.pipe_here = pipe_here
		self.module_names = module_names
		#self.dpi_setting = options.get("dpi")
		self.q = q

	def run_pre_processing(
			self,
			doc: Document,
		):
		"""
		Run pre-processing on a single document:
		Canonicizers, event drivers, event cullers.
		"""
		# doc: the document passed in.
		# dump_queue: when multi-processing,
		# the shared queue to temporarily store the documents.
		for c in self.backend_API.modulesInUse["Canonicizers"]:
			c._global_parameters = self.backend_API.global_parameters
			doc.text = c.process(doc.text)
		
		for e in self.backend_API.modulesInUse["EventDrivers"]:
			e._global_parameters = self.backend_API.global_parameters
			event_set = e.createEventSet(doc.text)
			doc.setEventSet(event_set, append=True)
		
		for ec in self.backend_API.modulesInUse["EventCulling"]:
			ec._global_parameters = self.backend_API.global_parameters
			doc.setEventSet(ec.process(doc.eventSet))
		return doc

	def run_experiment(self, **options):

		"""
		Process all input files with the parameters in all tabs.
		input: unknown authors, known authors, all listboxes.
		"""
		return_results = options.get("return_results", False)
		# check_listboxes:
		#   list of listboxes that shouldn't be empty.
		# check_labels:
		#   list of labels whose text colors need to be updated upon checking the listboxes.
		if GUI_debug >= 3: print("run_experiment()")


		# above is the code to change the color/available status of the "process" button.
		# below is the actual processing.

		# LOADING DOCUMENTS

		if self.pipe_here != None: self.pipe_here.send("Getting documents")

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

		if self.pipe_here != None: self.pipe_here.send("Pre-processing text")

		# PRE-PROCESSING
		if len(self.backend_API.documents) < self.gui_params["multiprocessing_limit_docs"]:
			# only use multi-processing when the number of docs is large.
			if GUI_debug >= 2: print("single-threading.")

			processed_docs = []
			total_num_docs = len(self.backend_API.documents)
			for doc_ind in range(total_num_docs):
				if self.pipe_here != None: self.pipe_here.send(int((doc_ind/total_num_docs)*100))
				pre_processed_doc = self.run_pre_processing(self.backend_API.documents[doc_ind])
				processed_docs.append(pre_processed_doc)
			self.backend_API.documents = processed_docs

		else:
			# TODO 1 priority high:
			# implement multi-processing for pre-processing.
			raise NotImplementedError
			if GUI_debug >= 2: print("multi-threading")
			process_list = []
			dump_queue = Queue()
			for doc in self.backend_API.documents:
				process_list.append(Process(target = run_pre_processing(doc, dump_queue)))
				process_list[-1].start()
			for proc in process_list:
				proc.join()
			self.backend_API.documents = []
			while not dump_queue.empty():
				doc_get = dump_queue.get()
				self.backend_API.documents.append(doc_get)

		# RUN ANALYSIS ON UNKNOWN DOCS
		# TODO 1 priority high:
		# implement multi-processing for analysis methods.
		# if $score < multiprocessing_limit_analysis:

		if self.pipe_here != None: self.pipe_here.send(0)

		# NUMBER CONVERSION: must take in all files in case there are author-based algorithms.
		

		results = []

		for nc in self.backend_API.modulesInUse["NumberConverters"]:
			"""
			Only one number converter used for one analysis method
			This means for N number converters and M methods, there will be (N x M) analyses.
			"""
			nc._global_parameters = self.backend_API.global_parameters

			all_data = nc.convert(known_docs + unknown_docs)
			known_docs_numbers_aggregate = all_data[:len(known_docs)]
			unknown_docs_numbers_aggregate = all_data[len(known_docs):]
			del all_data

			if GUI_debug >= 3: print("Running analysis methods")
			number_of_classifiers = len(self.backend_API.modulesInUse["AnalysisMethods"])
			for am_df_index in range(number_of_classifiers):
				#if GUI_debug >= 3: print("a")

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
				
				if self.pipe_here != None: self.pipe_here.send("Analyzing - %s" % am_df_names_display)

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

		if self.pipe_here != None: self.pipe_here.send(-1)
		
		if self.q != None:
			self.q.put(results_text)
			return 0
		if return_results:
			return results_text
		print(results_text)

