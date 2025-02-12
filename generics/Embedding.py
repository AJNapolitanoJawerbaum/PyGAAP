from abc import ABC, abstractmethod

# An abstract DistanceFunction class.
class Embedding(ABC):
	"""
	An embedder accepts the set of known documents
	and set the docs' representations directly to Document.numbers
	"""
	_global_parameters = dict()
	_default_multiprocessing = False

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


	def after_init(self, **options):
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

	@abstractmethod
	def convert(self, known_docs, pipe_here=None):
		'''Input is event set, output is numbers'''
		pass

	def displayName():
		'''Returns the display name for the given distance function.'''
		pass

	def displayDescription():
		pass

