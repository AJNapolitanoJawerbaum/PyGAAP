from generics.module import Embedding
# from backend.Histograms import generateAbsoluteHistogram as gh
# from backend import PrepareNumbers as pn
from multiprocessing import Pool, cpu_count
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from copy import deepcopy

# class Frequency(Embedding):

# 	normalization = "linear scale [0, 1]"
# 	_default_multiprocessing = False
# 	_variable_options = {
# 		"normalization": {"options": ["none", "linear scale [0, 1]"], "type": "OptionMenu", "default": 1,
# 		"displayed_name": "Normalization"}
# 	}

# 	def process(self, docs, pipe=None):
# 		"""Convert and assign to Documents.numbers"""
# 		if self._default_multiprocessing:
# 			with Pool(cpu_count()-1) as p:
# 				raw_frequency = p.map(gh, docs)
# 		else:
# 			raw_frequency = [gh(d) for d in docs]
# 		numbers = pn.dicts_to_array(raw_frequency)
# 		if self.normalization == "none": pass
# 		elif self.normalization == "linear scale [0, 1]":
# 			numbers = numbers/np.max(numbers, axis=1, keepdims=1)
# 		for d_index in range(len(docs)):
# 			docs[d_index].numbers = numbers[d_index:d_index+1,:][0]
# 		return numbers

# 	def displayDescription():
# 		return ("Converts events to their frequencies.\n" +\
# 			"linear scale [0, 1] in normalization means scaling values to [0, 1].\n\n" +\
# 			"If a doc's features are all zeros, normalization may result in NaNs.")

# 	def displayName():
# 		return "Frequency"


class Frequency(Embedding):
	normalization = "Global max"
	max_features = 0
	binary = 0
	_default_multiprocessing = False
	_variable_options = {
		"normalization": {"options": ["None", "Per-document token count", "Per-document max", "Global max"],
		"type": "OptionMenu", "default": 1, "displayed_name": "Normalization"},
		"max_features": {"options": range(0, 101), "type": "Slider", "default": 0, "displayed_name": "Max features"},
		"binary": {"options": [0, 1], "type": "Tick", "default": 0, "displayed_name": "Binary"}
	}

	def process(self, docs, pipe=None):
		"""Convert and assign to Documents.numbers"""

		mf = self.max_features if self.max_features > 0 else None
		bi = True if self.binary else False
		cv = CountVectorizer(lowercase=False, analyzer=lambda x:x, max_features=mf, binary=bi)

		numbers = cv.fit_transform([d.eventSet for d in docs]).toarray()

		if self.normalization == "None":
			# equivalent to JGAAP's absolute centroid driver
			pass
		elif self.normalization == "Per-document max":
			numbers = numbers / np.max(numbers, axis=1, keepdims=1)
		elif self.normalization == "Per-document token count":
			# equivalent to JGAAP's centroid driver
			numbers = numbers / np.sum(numbers, axis=1, keepdims=1)
		elif self.normalization == "Global max":
			numbers = numbers / np.max(numbers)
		# elif self.normalization == "Per-token max":
		# 	numbers = numbers / np.max(numbers, axis=0, keepdims=1)

		for d_index in range(len(docs)):
			# distribute aggregate results to each doc obj
			docs[d_index].numbers = numbers[d_index:d_index+1,:][0]
		return numbers

	def displayDescription():
		return (
			"Converts events to their frequencies, using sklearn's count vectorizer\n" +\
			"Normalization:\n\tNone: use raw token counts (with \"Centroid Driver\", equiv. to JGAAP's Absolute Centroid Driver)\n" +\
			"\tPer-document token count: divide counts by total number of tokens in each doc (with \"Centroid Driver\", equiv. to JGAAP's Centroid Driver)\n" +\
			"\tGlobal max: divide counts by the count of most-appeared token in a doc\n" +\
			"Max features: only tally top n tokens by raw counts. If zero, tally all.\n"+\
			"binary: use 0, 1 for token presence/absence instead of counting frequencies."
		)

	def displayName():
		return "Frequency"