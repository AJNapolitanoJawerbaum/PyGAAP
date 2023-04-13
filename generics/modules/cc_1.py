from generics.Canonicizer import Canonicizer
import re
import numpy as np
from unicodedata import normalize as unicode_normalize

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

	Language = None
	Version = None

	def after_init(self):
		self.Language = self._variable_options["Language"]["options"][self._variable_options["Language"]["default"]]
		self.Version = self._variable_options["Version"]["options"][self._variable_options["Version"]["default"]]

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

	def process_single(self, procText):
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
	def process_single(self, text):
		return "".join([x for x in text if x!="\t"])
	
	def displayDescription():
		return 'Strip tab characters "\\t".'
	
	def displayName():
		return "Strip Tabs"

class SmashI(Canonicizer):
	_pattern = re.compile("(^|\\W+)I(\\W+|$)")
	def process_single(self, text):
		return re.subn(self._pattern, "i", text)[0]

	def displayName():
		return "Smash I"
	
	def displayDescription():
		return "Replace capital I as a word to lowercase i."

class NormalizeUnicode(Canonicizer):
	latin = "Compose (NFC)"
	_variable_options = {
		"latin":
		{
			"options": ["Compose (NFC)", "Decompose (NFD)"],
			"type": "OptionMenu",
			"default": 0,
			"displayed_name": "Latin characters"
		},
	}
	def process_single(self, text):
		if self.type_ == "Compose (NFC)":
			return unicode_normalize("NFC", text)
		if self.type_ == "Decompose (NFD)":
			return unicode_normalize("NFD", text)

	def displayName():
		return "Normalize Unicode"
	
	def displayDescription():
		return "Convert to pre-composed or decomposed characters"

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
		
	# 	def process_single(self, procText):
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

# class Nothing(Canonicizer):
	
# 	Segment = 10

# 	_variable_options = {
# 		"Segment": {
# 			"options": ["10", "50", "full"],
# 			"type": "OptionMenu",
# 			"default": 0
# 		}
# 	}
# 	def displayDescription():
# 		return "Prints received file to terminal"
	
# 	def displayName():
# 		return "*"

# 	def process_single(self, text):
# 		if self.Segment == "full":
# 			print(text)
# 		else:
# 			print(text[int(self.Segment)])