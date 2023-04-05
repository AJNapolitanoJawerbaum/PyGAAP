from abc import ABC, abstractmethod
import re
from multiprocessing import Pool, cpu_count
import c_cc_0

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
	imp = "py"
	_variable_options = {"imp": {"options": ["py", "C++"], "default": 0, "displayed_name": "Implementation"}}
	_ps = {}

	def process_single(self, procText):
		'''Convert procText in to a string where all whitespace characters are the same.'''
		return ' '.join(procText.split())

	def process_single_C(self, text):
		return c_cc_0.normalize_ws_process_single(text)

	def after_init(self, **options):
		self._ps = {"py": self.process_single, "C++": self.process_single_C}

	def process(self, docs, pipe=None):
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				canon = p.map(self._ps[self.imp], [d.text for d in docs])
			for d in range(len(canon)):
				docs[d].canonicized = canon[d]
		else:
			for i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*i/len(docs))
				d.canonicized = self._ps[self.imp](d.text)
		return

	def displayName():
		return "Normalize Whitespace"

	def displayDescription():
		return "Converts whitespace characters to a single space.\n" +\
		"The py implementation uses Python's white-space char list for str.split()\n" +\
		"The C++ implementation checks for ascii white space characters."

class UnifyCase(Canonicizer):
	def process_single(self, procText):
		"""Convert procText to lower case"""
		return procText.lower()
	
	def displayName():
		return "Unify Case"

	def displayDescription():
		return "Converts all text to lower case."

class StripPunctuation(Canonicizer):
	full_width = 1
	_variable_options = {
		"full_width": {"options": [0, 1], "type": "Tick", "default": 1, "displayed_name": "Include full-width"}
	}
	_punct = re.compile(",.?!\"'`;:-()&$")
	_fw_punct = re.compile("，。？！“”‘’；：——（）、《》【】『』")
	def process_single(self, text):
		"""Gets rid of punctuation characters"""
		text = re.subn(self._punct, "", text)[0]
		#text = ''.join([char for char in text if char not in ",.?!\"'`;:-()&$"])
		if self.full_width:
			text = re.subn(self._fw_punct, "", text)[0]
		return text
	
	def displayDescription():
		return 'Strip a list of punctuations from the text:\n' +\
			',.?!"\'`;:-()&$\n' +\
			'Full-width punctuations include:\n"，。？！“”‘’；：——（）、《》【】『』"'

	def displayName():
		return "Strip Punctuation"

class StripNumbers(Canonicizer):
	chn_jpa = 0
	_variable_options = {
		"chn_jpa": {"options": [0, 1], "type": "Tick", "default": 0, "displayed_name": "Chinese/Japanese"}
	}

	_regex_match = re.compile("0+")
	# this over-covers cases, but the over-covered cases are malformed numerals.
	_chn_regex = re.compile("((([一二两三四五六七八九]*亿)|零)*(([一二两三四五六七八九]*千)|零)*(([一二两三四五六七八九]*百)|零)*"
		"(([一二两三四五六七八九]*十)|零)*(([一二两三四五六七八九]*万)|零)*(([一二两三四五六七八九]*千)|零)*"
		"(([一二两三四五六七八九]*百)|零)*(([一二三四五六七八九]*十)|零)*([一二三四五六七八九])*)+")

	def process_single(self, text):
		"""Converts each digit string to a single zero."""
		text = ''.join(["0" if char in "0123456789" else char for char in text])
		text = re.subn(self._regex_match, "0", text)[0]
		if self.chn_jpa:
			text = re.subn(self._chn_regex, "零", text)[0]
		return text

	def displayDescription():
		return "Converts each simple digit string to a single 0.\n" +\
			"Enabling Chinese/Japanese numerals converts all chinese-character numberals to the Chinese zero.\n" +\
			"\tThis does not include numerical characters used in accounting."

	def displayName():
		return "Strip Numbers"

class PunctuationSeparator(Canonicizer):
	full_width = 1
	_variable_options = {
		"full_width": {"options": [0, 1], "type": "Tick", "default": 1, "displayed_name": "Include full-width"}
	}
	_punct = ",.?!\"'`;:-()&$"
	_fw_punct = "，。？！“”‘’；：——（）、《》【】『』"
	def process_single(self, procText):
		"""Adds whitespaces before and after punctuations."""
		punctuations = self._punct + (self._fw_punct if self.full_width else "")
		return ''.join([" "+char+" " if char in punctuations else char for char in procText])
	
	def displayDescription():
		return "Adds whitespaces before and after punctuations.\n" +\
			'Full-width punctuations include:\n"，。？！“”‘’；：——（）、《》【】『』"'
	
	def displayName():
		return "Punctuation Separator"

class StripAlphanumeric(Canonicizer):
	full_width = 1
	_variable_options = {
		"full_width": {"options": [0, 1], "type": "Tick", "default": 1, "displayed_name": "Include full-width"}
	}
	_punct = ",.?!\"'`;:-()&$"
	_fw_punct = "，。？！“”‘’；：——（）、《》【】『』"
	def process_single(self, procText):
		"""Strips all non-whitespace, non-punctuation marks."""
		leave = " " + self._punct + (self._fw_punct if self.full_width else "")
		return ''.join([char for char in procText if char in leave])

	def displayDescription():
		return "Strips all non-whitespace, non-punctuation marks. i.e. leaves only white spaces and punctuation marks.\n"+\
			'Full-width punctuations include:\n"，。？！“”‘’；：——（）、《》【】『』"'
	
	def displayName():
		return "Strip Alpha-numeric"

class StripNullCharacters(Canonicizer):
	def process_single(self, procText):
		return ''.join([char for char in procText if char!="\0"])

	def displayDescription():
		return "Strips all 0x00 from the text."
	
	def displayName():
		return "Strip Null Characters"
