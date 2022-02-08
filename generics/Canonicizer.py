from abc import ABC, abstractmethod
import re
import numpy as np

# An abstract Canonicizer class.
class Canonicizer(ABC):
	_index=0

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

class CangjieConvertStripPunctuations(Canonicizer):
	# The initializing of the lookup table depends on a hard-coded number of lines in the lookup table text file.
	_lookupTable=np.empty_like(['abcde'], dtype="<U5", shape=(175135,))


	def __init__(self):
		lookupTableFile = open("./extra/canonicizer_CangjieConverter/CangjieConvertTable.txt")
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
		"""
		character_table_use.txt generated by a script that uses Debian's pycangjie library:
		https://salsa.debian.org/input-method-team/pycangjie
		The character table uses unicode for the Chinese characters' encoding.
		To update the character table, replace the file in /extra/canonicizer_CangjieConverter/CharacterTable.txt.
		To regenerate the character table, run /extra/canonicizer_CangjieConverter/CharacterTableGenerator.py
		.py.
		Caution: the character table generator has only been tested on Linux (Ubuntu).
		"""
		outText=""
		for character in procText:
			try:
				unicodeNumber = ord(character)
				code = self._lookupTable[unicodeNumber - 19968]
				outText+=code+" "
			except:
				continue
		return outText
	
	def displayDescription():
		return "Converts each Traditional or Simplified Chinese character to its Cangjie code, Stripping punctuations."

	def displayName():
		return "Cangjie-convert to letters (Strips punctuations)"

class CangjieConvertLeavePunctuations(Canonicizer):
	CangjieConvert=CangjieConvertStripPunctuations()
	_lookupTable=CangjieConvert._lookupTable
	def process(self, procText):
		"""
		Wrapper of CangjieConvertStripPunctuations but with different methods (see above)
		"""
		outText=""
		for character in procText:
			try:
				unicodeNumber = ord(character)
				code = self._lookupTable[unicodeNumber - 19968]
				outText+=code+" "
			except:
				outText+=character+" "
		return outText

	def displayDescription():
		return "Converts each Traditional or Simplified Chinese character to its Cangjie code, Leaving punctuations. Stripping numbers prior to this is highly recommended."

	def displayName():
		return "Cangjie-convert to letters (Leaves punctuations)"
