from generics.Embedding import Embedding
# from backend.Histograms import generateAbsoluteHistogram as gh
# from backend import PrepareNumbers as pn
from multiprocessing import Pool, cpu_count
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

# class Frequency(Embedding):

# 	normalization = "linear scale [0, 1]"
# 	_default_multiprocessing = False
# 	_variable_options = {
# 		"normalization": {"options": ["none", "linear scale [0, 1]"], "type": "OptionMenu", "default": 1,
# 		"displayed_name": "Normalization"}
# 	}

# 	def convert(self, docs, pipe=None):
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
	normalization = "Per-document max"
	max_features = 0
	binary = 0
	events = "known only"
	_default_multiprocessing = False
	_variable_options = {
		"normalization": {"options": ["None", "Per-document max", "Global max"], "type": "OptionMenu", "default": 1,
		"displayed_name": "Normalization"},
		"max_features": {"options": range(0, 101), "type": "Slider", "default": 0, "displayed_name": "Max features"},
		"events": {"options": ["Known events only", "All"], "default": 0, "displayed_name": "Analyze events"},
		"binary": {"options": [0, 1], "type": "Tick", "default": 0, "displayed_name": "Binary"}
	}

	def convert(self, docs, pipe=None):
		"""Convert and assign to Documents.numbers"""

		mf = self.max_features if self.max_features > 0 else None
		bi = True if self.binary else False
		cv = CountVectorizer(lowercase=False, analyzer=lambda x:x, max_features=mf, binary=bi)

		if self.events == "All":
			numbers = cv.fit_transform([d.eventSet for d in docs]).toarray()
		elif self.events == "Known events only":
			cv.fit([d.eventSet for d in docs if d.author != ""])
			numbers = cv.transform([d.eventSet for d in docs]).toarray()
		else: raise ValueError("Unknown option in Frequency: %s" % self.events)

		if self.normalization == "None": pass
		elif self.normalization == "Per-document max":
			numbers = numbers / np.max(numbers, axis=1, keepdims=1)
		elif self.normalization == "Global max":
			numbers = numbers / np.max(numbers)
		for d_index in range(len(docs)):
			docs[d_index].numbers = numbers[d_index:d_index+1,:][0]
		return numbers

	def displayDescription():
		return (
			"Converts events to their frequencies, using sklearn's count vectorizer\n" +\
			"linear scale [0, 1] in normalization means scaling values to [0, 1].\n\n" +\
			"Max features: only tally top n tokens by raw counts. If zero, tally all.\n"+\
			"binary: use 0, 1 for token presence/absence instead of counting frequencies."
		)

	def displayName():
		return "Frequency"