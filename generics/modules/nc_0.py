from generics.Embedding import Embedding
from backend.Histograms import generateAbsoluteHistogram as gh
from backend import PrepareNumbers as pn
from multiprocessing import Pool, cpu_count
import numpy as np

class Frequency(Embedding):

	normalization = "zero-max scaling"
	_default_multiprocessing = False
	_variable_options = {
		"normalization": {"options": ["none", "zero-max scaling"], "type": "OptionMenu", "default": 1,
		"displayed_name": "Statistical normalization"}
	}

	def convert(self, docs, pipe=None):
		"""Convert and assign to Documents.numbers"""
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as p:
				raw_frequency = p.map(gh, docs)
		else:
			raw_frequency = [gh(d) for d in docs]
		numbers = pn.dicts_to_array(raw_frequency)
		if self.normalization == "none": pass
		elif self.normalization == "zero-max scaling":
			numbers = numbers/np.max(numbers, axis=1, keepdims=1)
		for d_index in range(len(docs)):
			docs[d_index].numbers = numbers[d_index:d_index+1,:][0]
		return numbers

	def displayDescription():
		return ("Converts events to their frequencies.\n" +\
			"Zero-max scaling in normalization means scaling values to [0, 1].\n\n" +\
			"If a doc's features are all zeros, normalization may result in NaNs.")

	def displayName():
		return "Frequency"