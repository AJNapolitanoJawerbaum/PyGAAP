import csv, pathlib

from pandas import value_counts

ERROR_PREFIX = "Experiment CSV: "
def readCorpusCSV(csvPath, delimiter=","):
	'''Read the corpus csv at the given path in to a list of lists and return it.'''
	# Read each row from the CSV in to a list.
	csvRows = []
	with open(csvPath, "r") as file:
		readCSV = csv.reader(file, delimiter=delimiter)
		for row in readCSV:
			csvRows.append(row)
	return csvRows
	
def readExperimentCSV(csvPath, delimiter=","):
	'''
	Read the experiment CSV at the given path in to a list of lists and return it.
	Does some basic error checking.
	This is also compatible with JGAAP's experiment csv format.
	If number converter is missing, default to Frequency.
	'''
	csvRows = []
	with open(csvPath, "r") as file:
		readCSV = csv.reader(file, delimiter=delimiter)
		nRow = 0
		for row in readCSV:
			nRow += 1

			# error checking for every row
			if nRow > 1:
				if len(row) not in [6,7,8,9]:
					raise ValueError(ERROR_PREFIX + "Wrong number of columns. Perhaps a corpus csv was loaded instead?")
				elif len(row) == 6 or len(row) == 7:
					# 6 or 7 items: JGAAP csv format.
					# JGAAP allows for event cullers to be omitted.
					# 6 or 7 items to accomodate for files where the line ends with a comma.
					if len(row[-1]) == 0 and len(row[-2]) == 0:
						raise ValueError(ERROR_PREFIX + "No corpus csv for row %s (%s)" % (str(nRow), str(csvPath)))
					if row[2].strip() == "" or (row[3].strip() == "" and row[4].strip() == ""):
						raise ValueError(ERROR_PREFIX + "Missing event driver or analysis method")
				elif len(row) == 8 or len(row) == 9:
					# 8 or 9 items: PyGAAP csv format
					# PyGAAP requires all module types to be present.
					# 8 or 9 items to accomodate for files where the line ends with a comma.
					if len(row[-1]) == 0 and len(row[-2]) == 0:
						raise ValueError(ERROR_PREFIX + "No corpus csv for row %s (%s)" % (str(nRow), str(csvPath)))
					if row[2].strip() == "" and row[5].strip() == "":
						raise ValueError(ERROR_PREFIX + "Missing event driver or analysis method")
					if row[4].strip() == "":
						row[4] = "Frequency"
			csvRows.append(row)
	del csvRows[0]
	return csvRows
	
def findCorpusCSVPath(corpusCSVPathEntry):
	'''Find the corpus CSV's path based on the experiment CSV's path entry.'''
	return pathlib.Path(corpusCSVPathEntry).absolute()
	
def findDocumentPath(documentPathEntry):
	'''Find the path of the specified document based on the document path entry.'''
	return findCorpusCSVPath(documentPathEntry)
	
def readDocument(documentPath):
	'''Returns the contents of the document at the specified path.'''
	try:
		return pathlib.Path(documentPath).read_text()
	except UnicodeError:
		try:
			return pathlib.Path(documentPath).read_text(encoding="UTF-8")
		except UnicodeError:
			return pathlib.Path(documentPath).read_text(encoding="ISO-8859-15")
