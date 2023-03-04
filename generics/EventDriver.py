from abc import ABC, abstractmethod
from nltk import ngrams
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk import WordNetLemmatizer
from json import load as json_load
from pathlib import Path
from importlib import import_module
from multiprocessing import Pool, cpu_count
# import spacy

language_codes = json_load(f:=open(Path("./resources/languages.json"), "r"))
f.close()
del f

# An abstract EventDriver class.
class EventDriver(ABC):

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

	@abstractmethod
	def displayName():
		'''Returns the display name for the given event driver.'''
		pass
		
	@abstractmethod
	def setParams(self, params):
		'''Accepts a list of parameters and assigns them to the appropriate variables.'''

	@abstractmethod
	def displayDescription():
		pass
	
	def process(self, docs, pipe=None):
		"""Sets the events for the documents for all docs. Calls createEventSet for each doc."""
		if self._default_multiprocessing:
			if pipe is not None: pipe.send(True)
			with Pool(cpu_count()-1) as p:
				events = p.map(self.process_single, [d.canonicized for d in docs])
			for i in range(len(events)):
				docs[i].setEventSet(events[i])
		else:
			for i, d in enumerate(docs):
				if pipe is not None: pipe.send(100*i/len(docs))
				event_set = self.process_single(d.canonicized)
				d.setEventSet(event_set)
		return
	
	def process_single(self, procText):
		'''
		Processes a single document.
		This is no longer an abstract method because
		some modules may choose to ignore this function and deal with all documents instead in "process".
		'''
		raise NotImplementedError

	
# REFERENCE CLASS FOR PyGAAP GUI.
class CharacterNGramEventDriver(EventDriver):
	'''Event Driver for Character N-Grams'''
	n = 2
	_variable_options={"n": {"options": range(1, 21), "default": 1, "type": "Slider"}}
	# for PyGAAP GUI to know which options to list/are valid
		
	def process_single(self, procText):
		'''Returns a list containing the desired character n-grams.'''
		nltkRawOutput = list(ngrams(procText, self.n)) # This gives us a list of tuples.
		# Make the list of tuples in to a list of character fragments in the form of strings.
		formattedOutput = [''.join(val) for val in nltkRawOutput]
		if len(formattedOutput) == 0:
			raise ValueError("NLTK n-gram returned empty list. Check output of previous modules.")
		return formattedOutput
	
	def displayName():
		return "Character NGrams"
	
	def setParams(self, params):
		'''Sets the n parameter (length) for the Character N-Gram Event Driver. params is a list. '''
		self.n = params[0]

	def displayDescription(): # The text to display in PyGAAP GUI's description box.
		return "Groups of N successive characters (sliding window); N is given as a parameter."
	
		
class WhitespaceDelimitedWordEventDriver(EventDriver):
	'''Event Driver for Whitespace-Delimited Words'''
	
	def process_single(self, procText):
		'''Returns a list of words where a word is considered a whitespace-delimited unit.'''
		return procText.split()
		
	def displayName():
		return "Words (Whitespace-Delimited)"
	
	def setParams(self, params):
		'''This function is required, but does not do anything for this event driver.'''
		pass
		
	def displayDescription():
		return "Returns a list of words where a word is considered a whitespace-delimited unit."

class NltkWordTokenizerEventDriver(EventDriver):
	'''Event Driver for using the NLTK Word Tokenizer.'''
	
	def process_single(self, procText):
		'''Returns a list of words as defined by the NLTK Word Tokenizer.'''
		return word_tokenize(procText)
		
	def displayName():
		return "Words (NLTK Tokenizer)"
		
	def setParams(self, params):
		'''This function is required, but does not do anything for this event driver.'''
		pass

	def displayDescription():
		return "Word tokenizer using the Natural Language Took Kit's definition."
		
class SentenceEventDriver(EventDriver):
	'''Event Driver for getting sentences using the NLTK Sentence Tokenizer.'''
	
	def process_single(self, procText):
		'''Returns a list of sentences as defined by the NLTK Sentence Tokenizer.'''
		return sent_tokenize(procText)
		
	def displayName():
		return "Sentences"
		
	def setParams(self, params):
		'''This function is required, but does not do anything for this event driver.'''
		pass

	def displayDescription():
		return "Returns a list of sentences as defined by the NLTK Sentence Tokenizer."

class CharacterPositionEventDriver(EventDriver):
	'''Event Driver for letter positions. Only used on texts with delimited words (after canonicization).'''

	delimiter = "<whitespace(s)>"
	_variable_options = {"delimiter":
		{
			"options": ["<whitespace(s)>", ", (comma)", ". (period)", "; (semicolon)"],
			"type": "OptionMenu",
			"default": 0
		}
	}

	def process_single(self, procText):
		eventSet = []
		if self.delimiter == "<whitespace(s)>":
			splitText = procText.split()
		else:
			splitText = procText.split(self.delimiter[0])

		for word in splitText:
			eventSet += [str(word[letterIndex] + "_" + str(letterIndex)) for letterIndex in range(len(word))]
		return eventSet

	def setParams(self, params):
		'''This function is required, but does not do anything for this event driver.'''
		pass
	
	def displayName():
		return "Character Position"

	def displayDescription():
		return "Converts delimited words into list of letters with their positions within the word.\nRecommended with the Cangjie canonicizer"


# class WithinWordNGram(EventDriver):	
# 	_variable_options = {
# 		"delimiter":
# 		{
# 			"options": ["<whitespace(s)>", ", (comma)", ". (period)", "; (semicolon)"],
# 			"type": "OptionMenu",
# 			"default": 0
# 		},
# 		"n":
# 		{
# 			"options": list(range(4)),
# 			"type": "OptionMenu",
# 			"default": 0
# 		}
# 	}
# 	delimiter = _variable_options["delimiter"]["options"][_variable_options["delimiter"]["default"]]
# 	n = _variable_options["n"]["options"][_variable_options["n"]["default"]]
	
# 	def displayName():
# 		return "Within-word n-gram [under construction]"

# 	def displayDescription():
# 		return "Lists the n-gram of letter sequences within a word."

# 	def setParams(self, params):
# 		return


	# def process_single(self, procText):
	# 	eventSet = []
	# 	if self.delimiter == "<whitespace(s)>":
	# 		splitText = procText.split()
	# 	else:
	# 		splitText = procText.split(self.delimiter[0])

	# 	for word in splitText:
	# 		eventSet += [str(word[letterIndex] + "_" + str(letterIndex)) for letterIndex in range(len(word))]
	# 	return eventSet
	

class KSkipNGramCharacterEventDriver(EventDriver):
	_variable_options = {
		"k": {"options": range(1, 11), "type": "Slider", "default": 0, "displayed_name": "Skips (k)"},
		"n": {"options": range(1, 21), "type": "Slider", "default": 0, "displayed_name": "n-gram length (n)"}
	}
	k = 1
	n = 1

	def setParams(self, params):
		self.k = params[0]
		self.n = params[1]

	def displayDescription():
		return "n-gram extracted from text that only has every k characters from the original text."

	def displayName():
		return "K-skip Character N-gram"

	def process_single(self, text):
		text = "".join([text[i] for i in range(len(text)) if i%(self.k + 1) == 0])
		nltkRawOutput = list(ngrams(text, self.n))
		formattedOutput = [''.join(val) for val in nltkRawOutput]
		return formattedOutput

# PROBLEM: need to download vocab for tokenizing?

class WordNGram(EventDriver):
	n = 2
	tokenizer = "NLTK"
	#lemmatize = "No"

	_variable_options = {
		"n": {"options": range(1, 11), "type": "Slider", "default": 1, "validator": (lambda x: x >= 1 and x <= 20)},
		"tokenizer": {"options": ["Space delimiter", "SpaCy", "NLTK"], "type": "OptionMenu", "default": 1},
		#"lemmatize": {"options": ["No", "SpaCy", "NLTK"], "type": "OptionMenu", "default": 0, "displayed_name": "(N/A) lemmatize"}
	}

	def setParams(self, params):
		self.n, self.tokenizer, self.lemmatize = params

	def spacy_single(self, doc):
		'''spacy tokenize single doc'''
		# doc is the Document object.
		events = [str(token) for token in self._lang_module.tokenizer(doc.text)]
		return events

	def nltk_single(self, text):
		'''nltk tokenize single doc'''
		events = word_tokenize(text, language=self._nltk_lang)
		return events

	def process(self, docs, pipe):
		l = len(docs)
		if pipe is not None: pipe.send(True)
		if self.tokenizer == "SpaCy":
			lang = self._global_parameters["language_code"].get(self._global_parameters["language"], "eng")
			lang = language_codes.get(lang, "unk").get("spacy", "xx.MultiLanguage")
			self._lang_module = import_module("spacy.lang.%s" % lang.split(".")[0])
			self._lang_module = getattr(self._lang_module, lang.split(".")[1])()
			if self._default_multiprocessing:
				with Pool(cpu_count()-1) as p:
					events = p.map(self.spacy_single, docs)
				for i in range(len(docs)):
					docs[i].setEventSet(events[i])
			else:
				for i, d in enumerate(docs):
					if pipe is not None: pipe.send(100*i/l)
					d.setEventSet([str(token) for token in self._lang_module.tokenizer(d.text)])

		elif self.tokenizer == "NLTK":
			lang = self._global_parameters["language_code"].get(self._global_parameters["language"], "eng")
			self._nltk_lang = language_codes.get(lang, "unk").get("nltk", "english")
			if self._default_multiprocessing:
				with Pool(cpu_count()-1) as p:
					events = p.map(word_tokenize, [d.text for d in docs])
				for i in range(len(docs)):
					docs[i].setEventSet(events[i])
			else:
				for i, d in enumerate(docs):
					if pipe is not None: pipe.send(100*i/l)
					d.setEventSet(word_tokenize(d.text, language=self._nltk_lang))

		elif self.tokenizer == "Space delimiter":
			for i, d in enumerate(docs):
				d.setEventSet(d.text.split())
		else:
			raise ValueError("Unknown tokenizer type %s" % self.tokenizer)

	
	def displayName():
		return "Word n-grams"

	def displayDescription():
		return "Word n-grams."


