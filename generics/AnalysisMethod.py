from abc import ABC, abstractmethod, abstractproperty
import math

import backend.Histograms as histograms
from importlib import import_module


# An abstract AnalysisMethod class.
class AnalysisMethod(ABC):
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
	def train(self, knownDocuments):
		'''Train a model on the knownDocuments.'''
		pass
		
	@abstractmethod
	def analyze(self, unknownDocument):
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

class CentroidDriver(AnalysisMethod):
	_authorHistograms = None
	
	def train(self, knownDocuments):
		'''Get a mean normalized histogram for each known author.'''
		self._authorHistograms = histograms.generateKnownDocsMeanHistograms(histograms.generateKnownDocsNormalizedHistogramSet(knownDocuments))
		
	def analyze(self, unknownDocument):
		'''Compare a normalized histogram of unknownDocument against the normalized known document histograms and return a dictionary of distances.'''
		results = dict()
		for author, knownHist in self._authorHistograms.items():
			results[author] = self.distance.distance(histograms.normalizeHistogram(histograms.generateAbsoluteHistogram(unknownDocument)), knownHist)
		return results
	
	def displayName():
		return "Centroid Driver"

	def displayDescription():
		return "Computes one centroid per Author.\nCentroids are the average relative frequency of events over all documents provided.\ni=1 to n ΣfrequencyIn_i(event)."
