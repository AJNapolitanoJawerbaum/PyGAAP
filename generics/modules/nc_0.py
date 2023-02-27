from generics.NumberConverter import NumberConverter
from backend.Histograms import generateAbsoluteHistogram as gh
from backend import PrepareNumbers as pn
import numpy as np

class Frequency(NumberConverter):

	normalization = "zero-max scaling"

	_variable_options = {
		"normalization": {"options": ["none", "zero-max scaling"], "type": "OptionMenu", "default": 1,
		"displayed_name": "Statistical normalization"}
	}

	def convert(self, docs, pipe_here=None):
		"""Convert and assign to Documents.numbers"""
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