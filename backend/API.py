# import spacy
from importlib import import_module
from os import listdir as ls

class API:
	'''API class'''
	modules = []
	canonicizers = dict()
	eventDrivers = dict()
	analysisMethods = dict()
	distanceFunctions = dict()
	eventCulling = dict()
	numberConverters = dict()
	documents = []

	moduleTypeDict = {
		"Canonicizers": canonicizers,
		"EventDrivers": eventDrivers,
		"EventCulling": eventCulling,
		"NumberConverters": numberConverters,
		"AnalysisMethods": analysisMethods,
		"DistanceFunctions": distanceFunctions,
	}

	# these are lists of modules (and their params) added to the processing queue.
	# lists may contain multiple instances of the same module.
	# ! This currently only works for the GUI.
	modulesInUse = {
		"Canonicizers": [],
		"EventDrivers": [],
		"EventCulling": [],
		"NumberConverters": [],
		"AnalysisMethods": [],
		"DistanceFunctions": []
	}

	# TODO priority low:
	# allow modules to pass info along the pipeline:
	# e.g. if an event culler requires information on the text
	# before it was converted to the feature set.


	default_language = 0
	language_code = {
		# letter codes mostly follow ISO 639-3
		"English": "eng", "Chinese (simplified)": "zho", "Chinese (traditional)": "zht",
		"Spanish": "spa", "French": "fra", "German": "deu", "Japanese": "jpn",
		# "Italian": "ita", "Greek": "ell", "Russian": "rus", "Arabic": "ara", "Korean": "kor",
	}
	global_parameters = {"language": "English", "language_code": language_code}
	languages_available = list(language_code.keys())

	known_authors: list = [] # list used in GUI2 to keep track of known documents. LIST OF STRINGS
	unknown_docs: list = [] # list of unknown documents "Documents" (backend.Document). LIST OF DOCUMENTS

	default_mp = True # toggle built-in multiprocessing

	def __init__(self, documents):

		# delay importing modules to creation of API instance
		from generics.Canonicizer import Canonicizer
		from generics.EventCulling import EventCulling
		from generics.EventDriver import EventDriver
		from generics.NumberConverter import NumberConverter
		from generics.AnalysisMethod import AnalysisMethod
		from generics.DistanceFunction import DistanceFunction


		self.modules = []
		for item in ls("./generics/modules/"):
			if item[-3:] == ".py":
				self.modules.append(import_module("generics.modules.%s" % (item[:-3])))

		'''Build dictionaries of all the different parameters we can choose from.'''
		# Populate dictionary of canonicizers.
		for cls in Canonicizer.__subclasses__():
			if self.canonicizers.get(cls.displayName()) != None:
				raise ValueError("Two canonicizers can't both have the same displayed name: %s" % cls.displayName())
			self.canonicizers[cls.displayName()] = cls
		
		# Populate dictionary of event drivers.
		for cls in EventDriver.__subclasses__():
			if self.eventDrivers.get(cls.displayName()) != None:
				raise ValueError("Two event drivers can't both have the same displayed name: %s" % cls.displayName())
			self.eventDrivers[cls.displayName()] = cls

		# Populate dictionary of event culling.
		for cls in EventCulling.__subclasses__():
			if self.eventCulling.get(cls.displayName()) != None:
				raise ValueError("Two event cullers can't both have the same displayed name: %s" % cls.displayName())
			self.eventCulling[cls.displayName()] = cls

		for cls in NumberConverter.__subclasses__():
			if self.numberConverters.get(cls.displayName()) != None:
				raise ValueError("Two number converters can't both have the same displayed name: %s" % cls.displayName())
			self.numberConverters[cls.displayName()] = cls
		
		# Populate dictionary of analysis methods.
		for cls in AnalysisMethod.__subclasses__():
			if self.analysisMethods.get(cls.displayName()) != None:
				raise ValueError("Two analysis methods can't both have the same displayed name: %s" % cls.displayName())
			self.analysisMethods[cls.displayName()] = cls
		
		# Populate dictionary of distance functions.
		for cls in DistanceFunction.__subclasses__():
			if self.distanceFunctions.get(cls.displayName()) != None:
				raise ValueError("Two distance functions can't both have the same displayed name: %s" % cls.displayName())
			self.distanceFunctions[cls.displayName()] = cls
			
		# Set a list of documents for processing.
		self.documents = documents

		self.global_parameters = self.global_parameters

		# self.known_authors: list = []
		# self.unknown_docs: list = []

	def show_process_content(self):
		print("\nLanguage", self.global_parameters["language"], end="\n")
		print("Unknown_docs:\n")
		[print(str(d)) for d in self.unknown_docs]
		print("Known_authors:\n")
		[print(str(d)) for d in self.known_authors]
		print("Modules-in-use\n" + str(self.modulesInUse))
		return

	# def runCanonicizer(self, canonicizerString):
	# 	'''Runs the canonicizer specified by the string against all documents.'''
	# 	canonicizer = self.canonicizers.get(canonicizerString)()
	# 	for doc in self.documents:
	# 		doc.text = canonicizer.process(doc.text)
			
	# def runEventDriver(self, eventDriverString, **options):
	# 	'''Runs the event driver specified by the string against all documents.'''
	# 	eventDriver = self.eventDrivers.get(eventDriverString.split('|')[0])()
	# 	eventDriver.setParams(self._buildParamList(eventDriverString))
	# 	append = options.get("append", False)
	# 	for doc in self.documents:
	# 		doc.setEventSet(eventDriver.createEventSet(doc.text), append=append)
	
	# def runEventCuller(self):
	# 	raise NotImplementedError

	# def runNumberConverter(self):
	# 	raise NotImplementedError
			
	# def runAnalysis(self, analysisMethodString, distanceFunctionString):
	# 	'''Runs the specified analysis method with the specified distance function and returns the results.'''
	# 	analysis = self.analysisMethods.get(analysisMethodString)()
		
	# 	# Set the distance function to be used by the analysis method.
	# 	analysis.setDistanceFunction(self.distanceFunctions.get(distanceFunctionString))
		
	# 	# Identify the unknown document in the set of documents. The unknown document's author field will be an empty string.
	# 	unknownDoc = None
	# 	for document in self.documents:
	# 		if document.author == "":
	# 			unknownDoc = document
	# 			break
	# 	knownDocs = self.documents.copy()
	# 	knownDocs.remove(unknownDoc)
		
	# 	# Use the analysis to train and return the results of performing the analysis.
	# 	analysis.train(knownDocs)
	# 	return unknownDoc, analysis.analyze(unknownDoc)

	def prettyFormatResults(self, numberConverter, analysisMethod, distanceFunc, unknownDoc, results):
		'''Returns a string of the results in a pretty, formatted structure.'''
		# Build a string the contains general information about the experiment.
		formattedResults = str(unknownDoc.title) + ' ' + str(unknownDoc.filepath) + "\nCanonicizers:\n"
		for canonicizer in self.modulesInUse["Canonicizers"]:
			formattedResults += '\t' + canonicizer.__class__.displayName() + '\n'

		for eventDriver in self.modulesInUse["EventDrivers"]:
			formattedResults += "Event Drivers:\n\t" + eventDriver.__class__.displayName() + '\n'

		for eventCuller in self.modulesInUse["EventCulling"]:
			formattedResults += "Event Culler:\n\t" + eventCuller.__class__.displayName() + '\n'

		#for numberConverter in self.modulesInUse["NumberConverters"]:
		formattedResults += "Number Converter:\n\t" + numberConverter + '\n'

		formattedResults += "Analysis Method:\n\t" + analysisMethod +\
			" with " + distanceFunc + '\n'
		
		# Sort the dictionary in ascending order by distance values and build the results listing.
		orderedResults = {k: results[k] for k in sorted(results, key=results.get)}
		placement = 0
		prev = None
		for k, v in orderedResults.items():
			if prev == None or prev < v:
				placement += 1
				prev = v
			formattedResults += str(placement) + ". " + str(k) + ' ' + str(v) + '\n'
		
		return formattedResults
			
	def _buildParamList(self, eventDriverString):
		'''Builds and returns a list of parameter values that will be passed to an EventDriver.'''
		eventDriverString = eventDriverString.split('|')[1:]
		params = []
		[params.append(int(param.split(':')[1])) for param in eventDriverString]
		return params

	def set_global_parameters(self, parameter: str, string: str):
		"""Sets parameters to be used for all modules."""
		self.global_parameters[parameter] = string
		return