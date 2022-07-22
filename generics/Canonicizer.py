from abc import ABC, abstractmethod
import re
import numpy as np
from sklearn.multiclass import OutputCodeClassifier
# import spacy
from importlib import import_module

external_modules = {}
# external imports must use "backend.import_external"
for mod in external_modules:
	external_modules[mod] = import_module(mod)

# An abstract Canonicizer class.
class Canonicizer(ABC):
	_index = 0
	_global_parameters = dict()

	def __init__(self):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except:
			self._variable_options = dict()
		self._global_parameters = self._global_parameters

	@abstractmethod
	def process(self, procText):
		'''Input is original text and output is canonicized text.'''
		pass
		
	@abstractmethod
	def displayName():
		'''Returns the display name for the given canonicizer.'''
		pass

	@abstractmethod
	def displayDescription():
		'''Returns the display description for the canonicizer.'''
		
class NormalizeWhitespace(Canonicizer):
	def process(self, procText):
		'''Convert procText in to a string where all whitespace characters are the same.'''
		return ' '.join(procText.split())

	def displayName():
		return "Normalize Whitespace"

	def displayDescription():
		return "Converts all whitespace characters (newline, space and tab) to a single space.  Uses Java Character.isWhitespace for classification."

class UnifyCase(Canonicizer):
	def process(self, procText):
		"""Convert procText to lower case"""
		return procText.lower()
	
	def displayName():
		return "Unify Case"

	def displayDescription():
		return "Converts all text to lower case."

class StripPunctuation(Canonicizer):
	def process(self, procText):
		"""Gets rid of punctuation characters"""
		return ''.join([char for char in procText if char not in ",.?!\"'`;:-()&$"])
	
	def displayDescription():
		return 'Strip all punctuation characters (,.?!"\'`;:-()&$) from the text.'

	def displayName():
		return "Strip Punctuation"

class StripNumbers(Canonicizer):
	def process(self, procText):
		"""Converts each digit string to a single zero."""
		regex_match=re.compile("0+")
		procText=''.join(["0" for char in procText if char in "0123456789"])
		return re.subn(regex_match, "0", procText)[0]

	def displayDescription():
		return "Converts each simple digit string to a single 0"

	def displayName():
		return "Strip Numbers"

class PunctuationSeparator(Canonicizer):
	def process(self, procText):
		"""Adds whitespaces before and after punctuations."""
		return ''.join([" "+char+" " if char in ",.?!\"'`;:-()&$" else char for char in procText])
	
	def displayDescription():
		return "Adds whitespaces before and after punctuations."
	
	def displayName():
		return "Punctuation Separator"

class StripAlphanumeric(Canonicizer):
	def process(self, procText):
		"""Strips all non-whitespace, non-punctuation marks."""
		return ''.join([char for char in procText if char in " ,.?!\"'`;:-()&$"])

	def displayDescription():
		return "Strips all non-whitespace, non-punctuation marks. i.e. leaves only white spaces and punctuation marks."
	
	def displayName():
		return "Strip Alpha-numeric"

class StripNullCharacters(Canonicizer):
	def process(self, procText):
		return ''.join([char for char in procText if char!="\0"])

	def displayDescription():
		return "Strips all 0x00 from the text."
	
	def displayName():
		return "Strip Null Characters"

class CangjieConvert(Canonicizer):
	# The initializing of the lookup table depends on a hard-coded number of lines in the lookup table text file.
	_lookupTable=np.empty_like(['abcde'], dtype="<U5", shape=(175135,))

	_variable_options = {
		"Language":
		{
			"options": ["Chinese", "Japanese"],
			"type": "OptionMenu",
			"default": 0
		},
		"Version":
		{
			"options": ["3", "5"],
			"type": "OptionMenu",
			"default": 1
		}
	}


	def __init__(self):
		Language = self._variable_options["Language"]["options"][self._variable_options["Language"]["default"]]
		Version = self._variable_options["Version"]["options"][self._variable_options["Version"]["default"]]

		tableFilename = "./extra/canonicizer_CangjieConverter/CangjieConvertTable.txt"
		try:
			lookupTableFile = open(tableFilename)
		except UnicodeError:
			lookupTableFile = open(tableFilename, encoding="UTF-8")

		lookupRead = lookupTableFile.read().split("\n")
		lookupTableFile.close()
		
		for line in lookupRead:
			char = line.split(",")
			if len(char) == 1: continue
			try:
				self._lookupTable[int(char[1]) - 19968] = char[0]
			except:
				raise IndexError("CharacterTable.txt is longer than expected, please update the initialization of the table in Canonicizers.CangjieConvert.")
		return None

	def process(self, procText):
		outText=""
		lastCharConverted = False
		for character in procText:
			try:
				unicodeNumber = ord(character)
				code = self._lookupTable[unicodeNumber - 19968]
				if code != "" and unicodeNumber >= 19968:
					outText += code + " "
				else:
					outText += character + " "
				lastCharConverted == True
			except IndexError:
				if lastCharConverted:
					outText += character + " "
				else:
					outText = outText[:-1] + character + " "
		return outText

	def displayDescription():
		return "Converts Chinese/Japanese characters to Cangjie input codes.\n" \
			+ "The Cangjie input code encodes a character's spatial composition and its components.\n\n" \
			+ "Look up table generated by a script that uses Debian's pycangjie library:\n" \
			+ "https://salsa.debian.org/input-method-team/pycangjie \n" \
			+ "To update the character table, replace /extra/canonicizer_CangjieConverter/CangjieConvertTable.txt.\n" \
			+ "To regenerate the character table, run /extra/canonicizer_CangjieConverter/CharacterTableGenerator.py." \
			

	def displayName():
		return "Cangjie-convert"


class StripTabs(Canonicizer):
	def process(self, text):
		return "".join([x for x in text if x!="\t"])
	
	def displayDescription():
		return 'Strip tab characters "\\t".'
	
	def displayName():
		return "Strip Tabs"

	
	# class SpacyLemmatize(Canonicizer):
	# 	# class var.
	# 	_SpacyLemmatize_module_dict = {
	# 		"English": "en_core_web_sm",
	# 		"Chinese (GB2123)": "zh_core_web_sm",
	# 		"Japanese": "ja_core_news_sm",
	# 		# see https://spacy.io/usage/models
	# 		# for language module names.
	# 	}
	# 	# class var.
	# 	_SpacyLemmatize_lang_pipeline = None

	# 	def __init__(self):
	# 		return
			
	# 	def displayName():
	# 		return "Lemmatize (Spacy)"

	# 	def displayDescription():
	# 		return "Lemmatize words using the Spacy module."
		
	# 	def process(self, procText):
	# 		"""Lemmatize using spacy"""
	# 		print(self._SpacyLemmatize_module_dict)
	# 		if Canonicizer._SpacyLemmatize_lang_pipeline == None:
	# 			Canonicizer._SpacyLemmatize_lang_pipeline = spacy.load(
	# 				self._SpacyLemmatize_module_dict.get(
	# 					self._global_parameters["language"],
	# 					"xx_ent_wiki_sm"
	# 				)
	# 			)
	# 		lem = [
	# 			token.lemma_ for
	# 			token in
	# 			Canonicizer._spacy_lang_pipeline(procText)
	# 		]
	# 		lemmatized = " ".join(lem)
	# 		return lemmatized

class Nothing(Canonicizer):
	
	Segment = 10

	_variable_options = {
		"Segment": {
			"options": ["10", "50", "full"],
			"type": "OptionMenu",
			"default": 0
		}
	}
	def displayDescription():
		return "Prints received file to terminal"
	
	def displayName():
		return "_Nothing"

	def process(self, text):
		if self.Segment == "full":
			print(text)
		else:
			print(text[int(self.Segment)])