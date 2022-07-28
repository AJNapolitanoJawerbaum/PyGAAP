from abc import ABC, abstractmethod

# An abstract DistanceFunction class.
class NumberConverter(ABC):
	"""
	The number converter accepts the set of known documents
	and set the docs' representations directly to Document.numbers
	"""
	_global_parameters = dict()

	def __init__(self):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except:
			self._variable_options = dict()
		self._global_parameters = self._global_parameters
	@abstractmethod
	def convert(self, known_docs):
		'''Input is event set, output is numbers'''
		pass

	def displayName():
		'''Returns the display name for the given distance function.'''
		pass

	def displayDescription():
		pass

