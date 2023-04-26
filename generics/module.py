from abc import ABC, abstractmethod, abstractproperty
import numpy as np
from multiprocessing import Pool, cpu_count, Process, Pipe
import re
from unicodedata import normalize as unicode_normalize
import dictances as distances
from nltk import ngrams
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk import WordNetLemmatizer
from json import load as json_load
from pathlib import Path
from importlib import import_module
from sklearn.feature_extraction.text import CountVectorizer
from copy import deepcopy
from codecs import namereplace_errors

import backend.Histograms as histograms
from backend import PrepareNumbers as pn



class Module(ABC):
	"""The most generic module type. Does not appear in GUI, but inherited by all other module types."""

	_global_parameters = {}
	def __init__(self, **options):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except AttributeError:
			self._variable_options = dict()
		self._global_parameters = self._global_parameters
		try: self.after_init
		except (AttributeError, NameError): return
		self.after_init(**options)

	def after_init(self):
		return

	def in_out(self):
		"""returns input and output types. should match the process function"""
		return {"in": [], "out": []}

	@abstractmethod
	def process(self, process_input):
		return

	@abstractmethod
	def displayName():
		'''Returns the display name for the given analysis method.'''
		pass

	@abstractmethod
	def displayDescription():
		'''Returns the description of the method.'''
		pass

	def set_attr(self, var, value):
		"""Custom way to set attributes"""
		self.__dict__[var] = value

	def validate_parameter(self, param_name: str, param_value):
		"""validating parameter expects param_value to already been correctly typed"""
		if param_name not in self._variable_options:
			raise NameError("Unknown parameter in module")
		validator = self._variable_options[param_name].get("validator")
		if validator != None:
			val_result = validator(param_value)
			if not val_result: raise ValueError("Module parameter out of range")
		elif param_value not in self._variable_options[param_name]["options"]:
			raise ValueError("Module parameter out of range")
		return

	def process(self, docs, pipe=None, **options):
		"""generic process function. takes list of docs and return events"""
		if type(docs) not in [list, dict, set]:
			docs = [docs]
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				events = p.map(self.process_single, [d.canonicized for d in docs])
		else:
			events = []
			for i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*i/len(docs))
				events.append(self.process_single(d))
		return events

	def process_single():
		"""This is not an abstract method because it's optional."""
		raise NotImplementedError

class Generic_base(Module):
	_variable_options = dict()
	def displayName(): return "Generic_base"

class Math(Module):
    pass

# analysis
class AnalysisMethod(Module):
	
	'''
	The analysis method takes the known docs to train and predicts the labels of the unknown docs.
	It must be able to take one or a mix of dictinoaries, numpy arrays or scipy sparse arrays as training data.
	It calls backend.PrepareNumbers to make everything the same format.
	'''
	distance = None
	_variable_options = dict()
	_global_parameters = dict()
	_NoDistanceFunction_ = False

	def displayName(): return "AnalysisMethod"

	def get_train_data_and_labels(self, known_docs, train_data):
		"""get train data and labels, also sets self._labels_to_categories."""
		if train_data is None:
			train_data = tuple([d.numbers for d in known_docs])
			train_data = np.array(train_data)
		train_labels, self._labels_to_categories =\
			pn.auth_list_to_labels([d.author for d in known_docs])
		return train_data, train_labels

	def get_test_data(self, docs, options):
		"""
		Aggregate test data into a single matrix,
		designed to take parameters from document list input of analyze.
		"options" is the "options" parameter passed to the AnalysisMethod.process() function.
		"""
		return options.get("unknown_numbers") \
			if "unknown_nubmers" in options \
			else np.array([d.numbers for d in docs if d.author == ""])
	
	def get_results_dict_from_matrix(self, scores):
		"""
		returns the dictionary results per class from a scores matrix whose
		rows are test samples and whose columns are the known classes.
		"""
		if type(scores) != list:
			scores = scores.tolist()
		results = list()
		for doc in scores:
			doc_result = dict()
			for auth_index in range(len(doc)):
				doc_result[self._labels_to_categories[auth_index]] = doc[auth_index]
			results.append(doc_result)
		return results

	def setDistanceFunction(self, distance):
		'''Sets the distance function to be used by the analysis driver.'''
		self._distance = distance

	@abstractmethod
	def process(self, docs, pipe=None):
		return

# Canonicizer
class Canonicizer(Module):
	_index = 0
	_global_parameters = dict()
	_default_multiprocessing = True

	def displayName(): return "Canonicizer"

	def process(self, docs, pipe=None):
		"""
		process all docs at once, auto-call process_single.
		"""
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				canon = p.map(self.process_single, [d.text for d in docs])
			for d in range(len(canon)):
				docs[d].canonicized = canon[d]
		else:
			for i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*i/len(docs))
				d.canonicized = self.process_single(d.text)
		return


	def process_single(self, text):
		"""
		This is not an abstract method in the base class because
		it may not be present in some modules.
		Input/output of this may change. If changing input,
		also need to change the self.process() function.
		"""
		raise NotImplementedError
		

# Distance functions
class DistanceFunction(Module):
	_global_parameters = dict()

	def displayName(): return "DistanceFunction"

	@abstractmethod
	def distance(self, unknownHistogram, knownHistogram):
		'''
		Input is the unknown and known histograms and output is the resulting distance calculation.
		"knownHistogram" can be a per-author histogram or per-document histogram.
		'''
		pass


# An abstract Embedding class.
class Embedding(Module):
	"""
	An embedder accepts the set of known documents
	and set the docs' representations directly to Document.numbers
	"""
	_global_parameters = dict()
	_default_multiprocessing = False

	def displayName(): return "Embedding"

	@abstractmethod
	def process(self, known_docs, pipe_here=None):
		'''Input is event set, output is numbers'''
		pass



# An abstract Event Culling class.
class EventCulling(Module):

	_global_parameters = dict()
	_default_multiprocessing = True

	def displayName(): return "EventCulling"

	def process(self, docs, pipe):
		"""Process all docs"""
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				events = p.map(self.process_single, [d.eventSet for d in docs])
			for d in range(len(events)):
				docs[d].setEventSet(events[d], append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*d_i/len(docs))
				new_events = self.process_single(d.eventSet)
				d.setEventSet(new_events, append=False)
		return

	def process_single(self, eventSet):
		"""Process a single document"""
		raise NotImplementedError
		
# An abstract EventDriver class.
class EventDriver(Module):

	_global_parameters = dict()
	_default_multiprocessing = True

	def displayName(): return "EventDriver"

	@abstractmethod
	def setParams(self, params):
		'''Accepts a list of parameters and assigns them to the appropriate variables.'''

	def process(self, docs, pipe=None):
		"""Sets the events for the documents for all docs. Calls createEventSet for each doc."""
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				events = p.map(self.process_single, [d.canonicized for d in docs])
			for i in range(len(events)):
				docs[i].setEventSet(events[i])
		else:
			for i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*i/len(docs))
				event_set = self.process_single(d.canonicized)
				d.setEventSet(event_set)
		return
	
	def process_single(self, procText):
		'''
		Processes a single document.
		This is no longer an abstract method because
		some modules may choose to ignore this function and deal with all documents instead in "process".
		'''
		raise NotImplementedError
