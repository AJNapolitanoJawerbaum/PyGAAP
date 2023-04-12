# Move this file to ./generics/modules/ to test.
# All modules here raise errors while processing to test
# error-handling in backend.run_experiment.
# backend.run_experiment is expected not to crash because of errors here.
# @ author: Michael Fang

from generics.Canonicizer import Canonicizer
from generics.EventDriver import EventDriver
from generics.EventCulling import EventCulling
from generics.Embedding import Embedding
from generics.AnalysisMethod import AnalysisMethod
from generics.DistanceFunction import DistanceFunction


class Cc_error(Canonicizer):
	def process(self, docs, pipe=None):
		raise ValueError("Canonicizer exception message.")
	def displayName():
		return "Canonicizier Error Test."
	def displayDescription():
		return "Raises an error as a canonicizer."

class Ed_error(EventDriver):
	def process(self, docs, pipe=None):
		raise ValueError("Event Driver exception message.")
	def setParams(self, a, b):
		return
	def displayName():
		return "Event Driver Error Test."
	def displayDescription():
		return "Raises an error as an event driver."

class Ec_error(EventCulling):
	def process(self, docs, pipe=None):
		raise ValueError("Event Culler exception message.")
	def displayName():
		return "Event Culler Error Test."
	def displayDescription():
		return "Raises an error as an event culler."

class Nc_error(Embedding):
	def convert(self, docs, pipe=None):
		raise ValueError("Embedding exception message.")
	def displayName():
		return "Embedding Error Test."
	def displayDescription():
		return "Raises an error as an embedder."

class Am_error(AnalysisMethod):
	_NoDistanceFunction_ = True
	where = "analyze"
	_variable_options = {"where": {"options": ["train", "analyze"], "type": "OptionMenu", "default": 0}}
	def train(self, a, b, **c):
		if self.where == "train": raise ValueError("Analysis Method exception from train().")
		return
	def analyze(self, docs, pipe=None):
		if self.where == "analyze": raise ValueError("Analysis Method exception from analyze().")
	def displayName():
		return "Analysis Method (no distance) Error Test."
	def displayDescription():
		return "Raises an error as an analysis method."

class Am_df_error(AnalysisMethod):
	where = "analyze"
	_variable_options = {"where": {"options": ["train", "analyze"], "type": "OptionMenu", "default": 0}}
	def train(self, a, b, **c):
		if self.where == "train": raise ValueError("Analysis Method exception from train().")
		return
	def analyze(self, docs, pipe=None):
		if self.where == "analyze": raise ValueError("Analysis Method exception from analyze().")
	def displayName():
		return "Analysis Method (with distance) Error Test."
	def displayDescription():
		return "Raises an error as an analysis method."

class Df_error(DistanceFunction):
	def distance(self, unknown, known):
		raise ValueError("Distance Function exception message.")
	def displayName():
		return "Distance Function Error Test."
	def displayDescription():
		return "Raises an error as a distance function."
