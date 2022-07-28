from abc import ABC, abstractmethod, abstractproperty
import math

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
	
	def __init__(self):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except:
			self._variable_options = dict()	
		self._global_parameters = self._global_parameters

	@abstractmethod
	def train(self, knownDocuments, **options):
		'''Train a model on the knownDocuments.'''
		pass
		
	@abstractmethod
	def analyze(self, unknownDocuments):
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
		
	def setDistanceFunction(self, distance):
		'''Sets the distance function to be used by the analysis driver.'''
		self.distance = distance

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
	distance = None

	def setDistanceFunction(self, distance):
		'''Sets the distance function to be used by the analysis driver.'''
		self.distance = distance

	def train(self, known_docs, train_data=None):

		train_labels, self._labels_to_categories =\
			pn.auth_list_to_labels([d.author for d in known_docs])
		if train_data is None:
			# using "is" instead of "==" because numpy overloads "=="
			# as element-wise comparison

			# If none: did not use a vectorized number converter.
			# in this case, the representations are set in the texts,
			# no single matrix consisting of representation of all files were passed in.
			# need to recombine representations of the texts.
			train_data = tuple([d.numbers for d in known_docs])
		else:
			self._mean_per_author, self._means_labels =\
				pn.find_mean_per_author(train_data, train_labels)
		return

	def analyze(self, unknown_docs, unknown_docs_data=None):
		"""Get distance."""
		unknown_data = np.array([d.numbers for d in unknown_docs])
		doc_by_author = self.distance.distance(unknown_data, self._mean_per_author)
		results = list()
		for doc in doc_by_author:
			doc_result = dict()
			for auth_index in range(len(doc)):
				doc_result[self._labels_to_categories[auth_index]] = doc[auth_index]
			results.append(doc_result)
		return results
				


	def displayName():
		return "Centroid Driver"

	def displayDescription():
		return "[VECTORIZED]\nComputes one centroid per Author.\n" +\
			"Centroids are the average relative frequency of events over all documents provided.\n" +\
			"i=1 to n ΣfrequencyIn_i(event)."
