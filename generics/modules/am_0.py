from generics.AnalysisMethod import *



class CrossEntropy(AnalysisMethod):
	_NoDistanceFunction_ = True
	_histograms = None
	_histogramsNp = None
	_variable_options = {"mode": {"default": 0, "type": "OptionMenu", "options": ["author", "document"]}}
	_multiprocessing_score = 1
	mode = _variable_options["mode"]["options"][_variable_options["mode"]["default"]]

	def train(self, knownDocuments):
		if self.mode == "author":
			# authors -> mean histograms
			self._histograms = histograms.generateKnownDocsMeanHistograms(histograms.generateKnownDocsNormalizedHistogramSet(knownDocuments))
			#self._histogramsNp = {author:np.asarray(list(docHistogram.items())) for (author,docHistogram) in self._histograms.items()}
			# ^^ goes into the histogram list and change mean histograms into numpy arrays
		elif self.mode == 'document':
			# authors -> list of histograms
			self._histograms = histograms.generateKnownDocsNormalizedHistogramSet(knownDocuments)
			#self._histogramsNp = {author:[np.asarray(list(docHistogram.items())) for docHistogram in listOfHistograms] for (author,listOfHistograms) in self._histograms.items()}
			# ^^ goes into the list of histograms and individually change all histograms of all authors into numpy arrays
	def analyze(self, unknownDocument):
		# unknownDocument is a single doc, type Document.
		results=dict()
		unknownDocHistogram: dict = histograms.normalizeHistogram(histograms.generateAbsoluteHistogram(unknownDocument))
		#unknownDocHistogramNp = np.asarray(list(unknownDocHistogram.items()))
		results = dict()
		if self.mode == "author":
			for author in self._histograms:
				authorResult = 0 # numerial result for an author (mean histogram)
				for item in self._histograms[author]:
					if unknownDocHistogram.get(item) != None:
						authorResult -= self._histograms[author][item] * math.log(unknownDocHistogram[item])
				results[author] = authorResult

		elif self.mode == "document":
			for author in self._histograms:
				for doc in self._histograms[author]:
					docResult = 0 # numerical result for a single document
					for item in doc:
						if unknownDocHistogram.get(item) != None:
							docResult -= self._histograms[author][doc][item] * math.log(unknownDocHistogram[item])
					results[doc] = docResult
		return results
	
	def displayDescription():
		return "Discrete cross Entropy."
	
	def displayName():
		return "Cross Entropy"