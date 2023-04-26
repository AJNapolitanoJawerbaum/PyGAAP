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
	embeddings = dict()
	documents = []

	moduleTypeDict = {
		"Canonicizers": canonicizers,
		"EventDrivers": eventDrivers,
		"EventCulling": eventCulling,
		"Embeddings": embeddings,
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
		"Embeddings": [],
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
		from generics.module import Module, Canonicizer, EventCulling, EventDriver, Embedding, AnalysisMethod, DistanceFunction


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

		for cls in Embedding.__subclasses__():
			if self.embeddings.get(cls.displayName()) != None:
				raise ValueError("Two embedders can't both have the same displayed name: %s" % cls.displayName())
			self.embeddings[cls.displayName()] = cls
		
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

	def prettyFormatResults(self, embedding, analysisMethod, distanceFunc, unknownDoc, results):
		'''Returns a string of the results in a pretty, formatted structure.'''
		# Build a string the contains general information about the experiment.
		formattedResults = str(unknownDoc.title) + ' ' + str(unknownDoc.filepath) + "\nCanonicizers:\n"
		for canonicizer in self.modulesInUse["Canonicizers"]:
			formattedResults += '\t' + canonicizer.__class__.displayName() + '\n'

		for eventDriver in self.modulesInUse["EventDrivers"]:
			formattedResults += "Event Drivers:\n\t" + eventDriver.__class__.displayName() + '\n'

		for eventCuller in self.modulesInUse["EventCulling"]:
			formattedResults += "Event Culler:\n\t" + eventCuller.__class__.displayName() + '\n'

		#for embedding in self.modulesInUse["Embeddings"]:
		formattedResults += "Embedding:\n\t" + embedding + '\n'

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