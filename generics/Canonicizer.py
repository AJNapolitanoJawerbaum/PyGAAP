from abc import ABC, abstractmethod
import re
from multiprocessing import Pool, cpu_count

# An abstract Canonicizer class.
class Canonicizer(ABC):
	_index = 0
	_global_parameters = dict()
	_default_multiprocessing = True

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

	def process(self, docs, pipe=None):
		"""
		process all docs at once, auto-call process_single.
		"""
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				canon = p.map(self.process_single, [d.text for d in docs])
			for d in range(len(canon)):
				docs[d].canonicized = canon[d]
		else:
			for i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*i/len(docs))
				d.canonicized = self.process_single(d.text)
		return


	def process_single(self, text):
		"""
		This is not an abstract method in the base class because
		it may not be present in some modules.
		Input/output of this may change. If changing input,
		also need to change the self.process() function.
		"""
		raise NotImplementedError
		
	@abstractmethod
	def displayName():
		'''Returns the display name for the given canonicizer.'''
		pass

	@abstractmethod
	def displayDescription():
		'''Returns the display description for the canonicizer.'''
		
class NormalizeWhitespace(Canonicizer):
	def process_single(self, procText):
		'''Convert procText in to a string where all whitespace characters are the same.'''
		return ' '.join(procText.split())

	def displayName():
		return "Normalize Whitespace"

	def displayDescription():
		return "Converts all whitespace characters (newline, space and tab) to a single space.  Uses Java Character.isWhitespace for classification."

class UnifyCase(Canonicizer):
	def process_single(self, procText):
		"""Convert procText to lower case"""
		return procText.lower()
	
	def displayName():
		return "Unify Case"

	def displayDescription():
		return "Converts all text to lower case."

class StripPunctuation(Canonicizer):
	def process_single(self, procText):
		"""Gets rid of punctuation characters"""
		return ''.join([char for char in procText if char not in ",.?!\"'`;:-()&$"])
	
	def displayDescription():
		return 'Strip all punctuation characters (,.?!"\'`;:-()&$) from the text.'

	def displayName():
		return "Strip Punctuation"

class StripNumbers(Canonicizer):
	def process_single(self, procText):
		"""Converts each digit string to a single zero."""
		regex_match=re.compile("0+")
		procText=''.join(["0" if char in "0123456789" else char for char in procText])
		return re.subn(regex_match, "0", procText)[0]

	def displayDescription():
		return "Converts each simple digit string to a single 0"

	def displayName():
		return "Strip Numbers"

class PunctuationSeparator(Canonicizer):
	def process_single(self, procText):
		"""Adds whitespaces before and after punctuations."""
		return ''.join([" "+char+" " if char in ",.?!\"'`;:-()&$" else char for char in procText])
	
	def displayDescription():
		return "Adds whitespaces before and after punctuations."
	
	def displayName():
		return "Punctuation Separator"

class StripAlphanumeric(Canonicizer):
	def process_single(self, procText):
		"""Strips all non-whitespace, non-punctuation marks."""
		return ''.join([char for char in procText if char in " ,.?!\"'`;:-()&$"])

	def displayDescription():
		return "Strips all non-whitespace, non-punctuation marks. i.e. leaves only white spaces and punctuation marks."
	
	def displayName():
		return "Strip Alpha-numeric"

class StripNullCharacters(Canonicizer):
	def process_single(self, procText):
		return ''.join([char for char in procText if char!="\0"])

	def displayDescription():
		return "Strips all 0x00 from the text."
	
	def displayName():
		return "Strip Null Characters"
