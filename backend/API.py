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
	documents = []

	moduleTypeDict = {
		"Canonicizers": canonicizers,
		"EventDrivers": eventDrivers,
		"EventCulling": eventCulling,
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
		"AnalysisMethods": [],
		"DistanceFunctions": []
	}

	global_parameters = {"language": None}
	# TODO priority low:
	# allow modules to pass info along the pipeline:
	# e.g. if an event culler requires information on the text
	# before it was converted to the feature set.


	languages_available = ["English", "Arabic (ISO-8859-6)", "Chinese (GB2123)"]
	default_language = 0

	known_authors: list = [] # list used in GUI2 to keep track of known documents. LIST OF STRINGS
	unknown_docs: list = [] # list of unknown documents "Documents" (backend.Document). LIST OF DOCUMENTS


	def __init__(self, documents):

		# delay importing modules to creation of API instance
		from generics.Canonicizer import Canonicizer
		from generics.EventCulling import EventCulling
		from generics.EventDriver import EventDriver
		from generics.AnalysisMethod import AnalysisMethod
		from generics.DistanceFunction import DistanceFunction

		self.modules = []
		for item in ls("./generics/modules/"):
			if item[-3:] == ".py":
				self.modules.append(import_module("generics.modules.%s" % (item[:-3])))

		'''Build dictionaries of all the different parameters we can choose from.'''
		# Populate dictionary of canonicizers.
		for cls in Canonicizer.__subclasses__():
			self.canonicizers[cls.displayName()] = cls
		
		# Populate dictionary of event drivers.
		for cls in EventDriver.__subclasses__():
			self.eventDrivers[cls.displayName()] = cls

		# Populate dictionary of event culling.
		for cls in EventCulling.__subclasses__():
			self.eventCulling[cls.displayName()] = cls
		
		# Populate dictionary of analysis methods.
		for cls in AnalysisMethod.__subclasses__():
			self.analysisMethods[cls.displayName()] = cls
		
		# Populate dictionary of distance functions.
		for cls in DistanceFunction.__subclasses__():
			self.distanceFunctions[cls.displayName()] = cls
			
		# Set a list of documents for processing.
		self.documents = documents

		self.global_parameters = self.global_parameters

		#self.known_docs = []
		self.unknown_docs = []
		# TODO priority very low: use dictionary implementation
		# for unknown_docs.

		
	def runCanonicizer(self, canonicizerString):
		'''Runs the canonicizer specified by the string against all documents.'''
		canonicizer = self.canonicizers.get(canonicizerString)()
		for doc in self.documents:
			doc.text = canonicizer.process(doc.text)
			
	def runEventDriver(self, eventDriverString, **options):
		'''Runs the event driver specified by the string against all documents.'''
		eventDriver = self.eventDrivers.get(eventDriverString.split('|')[0])()
		eventDriver.setParams(self._buildParamList(eventDriverString))
		append = options.get("append", False)
		for doc in self.documents:
			doc.setEventSet(eventDriver.createEventSet(doc.text), append=append)
	
	def runEventCuller(self):
		raise NotImplementedError
			
	def runAnalysis(self, analysisMethodString, distanceFunctionString):
		'''Runs the specified analysis method with the specified distance function and returns the results.'''
		analysis = self.analysisMethods.get(analysisMethodString)()
		
		# Set the distance function to be used by the analysis method.
		analysis.setDistanceFunction(self.distanceFunctions.get(distanceFunctionString))
		
		# Identify the unknown document in the set of documents. The unknown document's author field will be an empty string.
		unknownDoc = None
		for document in self.documents:
			if document.author == "":
				unknownDoc = document
				break
		knownDocs = self.documents.copy()
		knownDocs.remove(unknownDoc)
		
		# Use the analysis to train and return the results of performing the analysis.
		analysis.train(knownDocs)
		return unknownDoc, analysis.analyze(unknownDoc)
		
	def prettyFormatResults(self, canonicizers, eventDrivers, eventCullers, analysisMethod, distanceFunc, unknownDoc, results):
		'''Returns a string of the results in a pretty, formatted structure.'''
		# Build a string the contains general information about the experiment.
		formattedResults = str(unknownDoc.title) + ' ' + str(unknownDoc.filepath) + "\nCanonicizers:\n"
		for canonicizer in canonicizers:
			formattedResults += '\t' + canonicizer + '\n'
		if type(eventDrivers) == list:
			for eventDriver in eventDrivers:
				formattedResults += "Event Drivers:\n\t" + eventDriver + '\n'
		else:
			formattedResults += "Event Driver:\n\t" + eventDrivers + '\n'

		for eventCuller in eventCullers:
			formattedResults += "Event Culler:\n\t" + eventCuller + '\n'

		formattedResults += "Analysis Method:\n\t" + analysisMethod + " with " + distanceFunc + '\n'
		
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