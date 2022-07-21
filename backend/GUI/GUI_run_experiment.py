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
from tkinter import *
from copy import deepcopy
from copy import copy as shallowcopy

import datetime
from json import load as json_load

from backend import API


from backend.CSVIO import readDocument
from backend.Document import Document


GUI_debug = 0

class Experiment:

	backend_API = None
	module_names: dict = {}

	def __init__(self, api, module_names: dict, dpi_setting, pipe_here=None, q:Queue=None):
		"""
		Copies API (So the main process can modify the original)
		receives an end of a pipe to send info back to main process.
		"""
		self.gui_params = json_load(f:=open("./backend/GUI/gui_params.json", "r"))
		f.close()
		self.backend_API = deepcopy(api)
		self.pipe_here = pipe_here
		self.module_names = module_names
		self.dpi_setting = dpi_setting
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
			#print("evset----------------", doc.eventSet[:15])
		
		if len(self.backend_API.modulesInUse["EventCulling"]) != 0:
			raise NotImplementedError
			#?._global_parameters = self.backend_API.global_parameters
		return doc

	def run_experiment(self):

		"""
		Process all input files with the parameters in all tabs.
		input: unknown authors, known authors, all listboxes.
		"""

		# check_listboxes:
		#   list of listboxes that shouldn't be empty.
		# check_labels:
		#   list of labels whose text colors need to be updated upon checking the listboxes.
		if GUI_debug >= 3: print("run_experiment()")


		# above is the code to change the color/available status of the "process" button.
		# below is the actual processing.

		# LOADING DOCUMENTS

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

		# PRE-PROCESSING
		if len(self.backend_API.documents) < self.gui_params["multiprocessing_limit_docs"]:
			# only use multi-processing when the number of docs is large.
			if GUI_debug >= 2: print("single-threading.")

			processed_docs = []
			total_num_docs = len(self.backend_API.documents)
			for doc_ind in range(total_num_docs):
				self.pipe_here.send(int((doc_ind/total_num_docs)*100))
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

		self.pipe_here.send(0)

		results = []
		if GUI_debug >= 3: print("Running analysis methods")
		number_of_classifiers = len(self.backend_API.modulesInUse["AnalysisMethods"])
		for am_df_index in range(number_of_classifiers):
			#if GUI_debug >= 3: print("a")

			am_df_pair = (self.backend_API.modulesInUse["AnalysisMethods"][am_df_index],
						self.backend_API.modulesInUse["DistanceFunctions"][am_df_index])
			am_df_pair[0]._global_parameters = self.backend_API.global_parameters
			if am_df_pair[1] != "NA":
				am_df_pair[1]._global_parameters = self.backend_API.global_parameters

			am_df_names_display = self.module_names["am_df_names"][am_df_index]
			if am_df_names_display[1] == "NA": am_df_names_display = am_df_names_display[0]
			else: am_df_names_display = am_df_names_display[0] + ', ' + am_df_names_display[1]
			self.pipe_here.send("Training - %s" % str(am_df_names_display))

			am_df_pair[0].setDistanceFunction(am_df_pair[1])
			
			# for each method: first train models on known docs
			am_df_pair[0].train(known_docs)
			# then for each unknown document, analyze and output results
			
			self.pipe_here.send("Analyzing - %s" % am_df_names_display)

			for d_index in range(len(unknown_docs)):

				d = unknown_docs[d_index]
				if d.author != "": continue

				self.pipe_here.send(int(100*d_index/len(unknown_docs)))
				doc_result = am_df_pair[0].analyze(d)
				formatted_results = \
					self.backend_API.prettyFormatResults(self.module_names["canonicizers_names"],
													self.module_names["event_drivers_names"],
													self.module_names["am_df_names"][am_df_index][0],
													self.module_names["am_df_names"][am_df_index][1],
													d,
													doc_result)
				results.append(formatted_results)
		
		
		results_text = ""
		for r in results:
			results_text += str(r + "\n")

		self.pipe_here.send(-1)
		
		self.q.put(results_text)
		return 0

