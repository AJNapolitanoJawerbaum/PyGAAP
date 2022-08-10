from abc import ABC, abstractmethod
from nltk import ngrams
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk import WordNetLemmatizer
from json import load as json_load
from pathlib import Path
from importlib import import_module
# import spacy

spacy_language_codes = json_load(f:=open(Path("./resources/spacy/languages.json"), "r"))
f.close()
del f

# An abstract EventDriver class.
class EventDriver(ABC):

	_global_parameters = dict()

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
	
	def process(self, docs, pipe):
		"""Sets the events for the documents for all docs. Calls createEventSet for each doc."""
		for d_i in range(l:=len(docs)):
			d = docs[d_i]
			if pipe is not None: pipe.send(100*d_i/l)
			event_set = self.process_single(d.text)
			d.setEventSet(event_set)
	
	def process_single(self, procText):
		'''
		Processes a single document.
		This is no longer an abstract method because
		some modules may choose to deal with all documents in "process".
		'''
		pass

	
# REFERENCE CLASS FOR PyGAAP GUI.
class CharacterNGramEventDriver(EventDriver):
	'''Event Driver for Character N-Grams'''
	n = 2
	_variable_options={"n": {"options": list(range(1, 21)), "default": 1, "type": "OptionMenu"}}
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


class WithinWordNGram(EventDriver):	
	_variable_options = {
		"delimiter":
		{
			"options": ["<whitespace(s)>", ", (comma)", ". (period)", "; (semicolon)"],
			"type": "OptionMenu",
			"default": 0
		},
		"n":
		{
			"options": list(range(4)),
			"type": "OptionMenu",
			"default": 0
		}
	}
	delimiter = _variable_options["delimiter"]["options"][_variable_options["delimiter"]["default"]]
	n = _variable_options["n"]["options"][_variable_options["n"]["default"]]
	
	def displayName():
		return "Within-word n-gram [under construction]"

	def displayDescription():
		return "Lists the n-gram of letter sequences within a word."

	def setParams(self, params):
		return


	def process_single(self, procText):
		eventSet = []
		if self.delimiter == "<whitespace(s)>":
			splitText = procText.split()
		else:
			splitText = procText.split(self.delimiter[0])

		for word in splitText:
			eventSet += [str(word[letterIndex] + "_" + str(letterIndex)) for letterIndex in range(len(word))]
		return eventSet
	

class KSkipNGramCharacterEventDriver(EventDriver):
	_variable_options = {
		"k": {"options": list(range(1, 11)), "type": "OptionMenu", "default": 0, "displayed_name": "Skips (k)"},
		"n": {"options": list(range(1, 21)), "type": "OptionMenu", "default": 0, "displayed_name": "n-gram length (n)"}
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
	lemmatize = "No"

	_variable_options = {
		"n": {"options": list(range(1, 11)), "type": "OptionMenu", "default": 1, "validator": (lambda x: x >= 1 and x <= 20)},
		"tokenizer": {"options": ["Space delimiter", "SpaCy", "NLTK"], "type": "OptionMenu", "default": 1},
		"lemmatize": {"options": ["No", "SpaCy", "NLTK"], "type": "OptionMenu", "default": 0, "displayed_name": "(N/A) lemmatize"}
	}

	def setParams(self, params):
		self.n, self.tokenizer, self.lemmatize = params

	def process_single(self, text: str):
		if self.tokenizer == "SpaCy":
			lang = self._global_parameters["language_code"][self._global_parameters["language"]]
			lang = spacy_language_codes.get(lang, "unk")
			lang_module = import_module("spacy.lang.%s" % lang.split(".")[0])
			lang_tokenizer = getattr(lang_module, lang.split(".")[1])
			lang_tokenizer = lang_tokenizer()
			tokens = lang_tokenizer(text)
			tokens = [str(t) for t in tokens]
		elif self.tokenizer == "NLTK":
			tokens = text.split()
		elif self.tokenizer == "Space delimiter":
			return text.split()
		else:
			raise ValueError("Unknown tokenizer option for Word n-grams: %s" % self.tokenizer)
		if self.lemmatize == "SpaCy":
			...
		elif self.lemmatize == "NLTK":
			...
		return tokens
	
	def displayName():
		return "Word n-grams"

	def displayDescription():
		return "Word n-grams."


