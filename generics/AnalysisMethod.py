from abc import ABC, abstractmethod, abstractproperty
from codecs import namereplace_errors

import backend.Histograms as histograms
from backend import PrepareNumbers as pn
import numpy as np


# An abstract AnalysisMethod class.
class AnalysisMethod(ABC):
	
	'''
	The analysis method takes the known docs to train and predicts the labels of the unknown docs.
	It must be able to take one or a mix of dictinoaries, numpy arrays or scipy sparse arrays as training data.
	It calls backend.PrepareNumbers to make everything the same format.
	'''
	distance = None
	_variable_options = dict()
	_global_parameters = dict()
	
	def __init__(self, **options):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except AttributeError:
			self._variable_options = dict()	
		self._global_parameters = self._global_parameters
		try: self.after_init(**options)
		except (AttributeError, NameError): pass

	def after_init(self, **options):
		pass

	@abstractmethod
	def train(self, train, train_data=None, **options):
		'''Train a model on the knownDocuments.'''
		pass
		
	@abstractmethod
	def analyze(self, test, test_data=None, **options):
		'''Analyze unknownDocument'''
		pass

	@abstractmethod
	def displayName():
		'''Returns the display name for the given analysis method.'''
		pass

	@abstractmethod
	def displayDescription():
		'''Returns the description of the method.'''
		pass

	# def set_attr(self, var, value):
	# 	"""Custom way to set attributes
	# 	(good for when setting a parameter changes the list of parameters itself)
	# 	return a boolean for whether to use the GUI's built-in way to set attributes after.
	# 	Default is to let the GUI set parameters."""
	# 	return True

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
	
	def get_train_data_and_labels(self, known_docs, train_data):
		"""get train data and labels, also sets self._labels_to_categories."""
		if train_data is None:
			train_data = tuple([d.numbers for d in known_docs])
			train_data = np.array(train_data)
		train_labels, self._labels_to_categories =\
			pn.auth_list_to_labels([d.author for d in known_docs])
		return train_data, train_labels

	def get_test_data(self, unknown_docs):
		"""
		Aggregate test data into a single matrix,
		designed to take parameters from document list input of analyze.
		"""
		return np.array([d.numbers for d in unknown_docs])
	
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

# class CentroidDriver_original(AnalysisMethod):
# 	_authorHistograms = None
	
# 	def train(self, knownDocuments):
# 		'''Get a mean normalized histogram for each known author.'''
# 		self._authorHistograms = histograms.generateKnownDocsMeanHistograms(histograms.generateKnownDocsNormalizedHistogramSet(knownDocuments))

# 	def analyze(self, unknownDocuments):
# 		'''Compare a normalized histogram of unknownDocument against the normalized known document histograms and return a dictionary of distances.'''
# 		docs_results = list()
# 		for d in unknownDocuments:
# 			results = dict()
# 			for author, knownHist in self._authorHistograms.items():
# 				results[author] = self.distance.distance(histograms.normalizeHistogram(histograms.generateAbsoluteHistogram(d)), knownHist)
# 			docs_results.append(results)
# 		return docs_results
	
# 	def displayName():
# 		return "Centroid Driver*"

# 	def displayDescription():
# 		return "Computes one centroid per Author.\nCentroids are the average relative frequency of events over all documents provided.\ni=1 to n ΣfrequencyIn_i(event)."

class CentroidDriver(AnalysisMethod):
	"""The version of centroid driver that pairs with the number converters"""

	_labels_to_categories = dict()
	_mean_per_author = dict()
	_means_labels = None
	_distance = None

	def train(self, known_docs, train_data=None):

		train_data, train_labels = self.get_train_data_and_labels(known_docs, train_data)
		self._mean_per_author, self._means_labels =\
			pn.find_mean_per_author(train_data, train_labels)
		return

	def analyze(self, unknown_docs, unknown_data=None):
		"""Get distance."""
		if unknown_data is None:
			unknown_data = self.get_test_data(unknown_docs)
		doc_by_author = self._distance.distance(unknown_data, self._mean_per_author)
		results = self.get_results_dict_from_matrix(doc_by_author)
		return results

	def displayName():
		return "Centroid Driver"

	def displayDescription():
		return "[VECTORIZED]\nComputes one centroid per Author.\n" +\
			"Centroids are the average relative frequency of events over all documents provided.\n" +\
			"i=1 to n ΣfrequencyIn_i(event)."

class KNearestNeighbor(AnalysisMethod):
	_document_embeddings: np.array = None
	_labels_to_categories = None
	_train_labels = None
	_distance = None
	k = 5
	tie_breaker = "average"
	_variable_options = {
		"k": {"options": list(range(1, 21)), "type": "OptionMenu", "default": 4, "displayed_name": "K"},
		"tie_breaker": {"options": ["average", "minimum"], "type": "OptionMenu", "default": 0, "displayed_name": "Tie breaker"}
	}
	def displayName():
		return "K-Nearest Neighbors"

	def displayDescription():
		return "This finds the K nearest documents in the feature space and assigns the class with most docs among them.\n" +\
			"Tie breakers:\n\taverage: the category with the smallest average\n\tminimum: category of the closest document among the ties."

	def train(self, known_docs, train_data=None, **options):
		train_data, self._train_labels = self.get_train_data_and_labels(known_docs, train_data)
		self._document_embeddings = train_data

	def analyze(self, unknown_docs, unknown_data=None, **options):
		"""
		K-nearest neighbor analysis implementation:\n
		This uses the usual algorithm for K-NN, where the class/category/author
		with the most votes from the K-nerest neighbors is assigned.
		Votes always out-rank the distance: this is ensured by calculating the votes
		and the distances separately, scaling the distances (per-doc on analysis) to [0, 0.5],
		and calculating the final author score using ```max_vote - votes + tie_breaking_distance.````\n
		Since the tie-breaker never exceeds 0.5, it will only affect ranking if two classes receive
		the same number of votes.
		"""
		if unknown_data is None:
			unknown_data = self.get_test_data(unknown_docs)
		labels = self._train_labels.flatten().tolist()
		unknown_by_known = self._distance.distance(unknown_data, self._document_embeddings)
		unknown_by_known = [[[u_doc[d], labels[d]] for d in range(len(u_doc))] for u_doc in unknown_by_known]
		unknown_by_known = [sorted(x)[:self.k] for x in unknown_by_known]

		unknown_by_authors = []
		for doc in unknown_by_known:
			doc_dict = dict()
			for auth in doc:
				doc_dict[auth[1]] = doc_dict.get(auth[1], []) + [auth[0]]
			if self.tie_breaker == "average":
							# votes				average
				doc_list = [[len(doc_dict[a]), sum(doc_dict[a])/len(doc_dict[a]), a] for a in doc_dict]
			elif self.tie_breaker == "minimum":
							# votes				closest score
				doc_list = [[len(doc_dict[a]), min(doc_dict[a]), a] for a in doc_dict]
			doc_list.sort(); doc_list.reverse()
			max_vote = doc_list[0][0]
			doc_list = {self._labels_to_categories[auth[2]]:max_vote-auth[0]+auth[1]/(2*max([a[1] for a in doc_list])) for auth in doc_list}
			unknown_by_authors.append(doc_list)
		return unknown_by_authors