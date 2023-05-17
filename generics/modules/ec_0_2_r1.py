"""
Implementation of several Event Cullers.
Most Common Events, Least Common Events, Coefficient of Variation, implemented by @Alejandro Napolitano Jawerbaum
"""
from generics.EventCulling import EventCulling 
from multiprocessing import Pool, cpu_count
from sklearn.feature_extraction.text import CountVectorizer
import numpy, scipy, data, stats

class MostCommonEvents(EventCulling):
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 50, "type": "OptionMenu", "default": 50}
    }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	
	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._sortedEventSet]

	def preprocess(self, docs):
		"""saves n most common events in self._sortedEventSet"""
		totalEventSet = dict()
		for d in docs:
			#if d.author is None or d.author == "": continue
			for e in d.eventSet:
				totalEventSet[e] = totalEventSet.get(e, 0) + 1
		self._sortedEventSet = sorted(
			totalEventSet, key=lambda i: totalEventSet[i], reverse=1
		)[:self.numEvents]
		return

	def process(self, docs, pipe=None):
		self.preprocess(docs)
		with Pool(cpu_count()-1) as p:
			new_events = p.map(self.process_single, docs)
		for d_i, d in enumerate(docs):
			# new_events = self.process_single(d.eventSet)
			d.setEventSet(new_events[d_i], append=False)
		return

	def displayName():
		return "Most Common Events"

	def displayDescription():
		return "Analyze only the N most frequent events across all documents."
    
class LeastCommonEvents(EventCulling):

	"""Least Common Events creates Most Common Events (above) and calls its functions"""

	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 50, "type": "OptionMenu", "default": 50}
    }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._sortedEventSet]

	def preprocess(self, docs):
		"""saves n most common events in self._sortedEventSet"""
		totalEventSet = dict()
		for d in docs:
			#if d.author is None or d.author == "": continue
			for e in d.eventSet:
				totalEventSet[e] = totalEventSet.get(e, 0) + 1
		self._sortedEventSet = sorted(
			totalEventSet, key=lambda i: totalEventSet[i], reverse=0
		)[:self.numEvents]
		return

	def process(self, docs, pipe=None):
		self.preprocess(docs)
		with Pool(cpu_count()-1) as p:
			new_events = p.map(self.process_single, docs)
		for d_i, d in enumerate(docs):
			# new_events = self.process_single(d.eventSet)
			d.setEventSet(new_events[d_i], append=False)
		return

	def displayName():
		return "Least Common Events"

	def displayDescription():
		return "Analyze only the N least frequent events across all documents."

class ExtremeCuller(EventCulling):

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self.extremeEvents]

	def process(self, docs, pipe=None):
		"""Process all docs"""

		# get set of events common in all docs, including test set
		self.extremeEvents = set(docs[0].eventSet)
		for d in docs[1:]:
			self.extremeEvents = self.extremeEvents.intersection(set(d.eventSet))
		#print(self.extremeEvents)
		if len(self.extremeEvents) == 0:
			raise ValueError("No events to analyze because there is no single event common in all docs.")

		# filter events. only leave those also in extremeEvents.
		with Pool(cpu_count()-1) as p:
			new_events = p.map(self.process_single, docs)
		for d_i, d in enumerate(docs):
			d.setEventSet(new_events[d_i], append=False)
		return

	def displayName():
		return "Extreme Culler"

	def displayDescription():
		return "Return only the events that appear in all samples, as suggested by (Jockers, 2008)"
    
    
class MeanAbsoluteDeviation(EventCulling):
	"""Mean absolute difference between a feature's frequency across docs and the mean frequency over all docs"""
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		mads = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		mads = numpy.mean(abs(
			event_frequencies-numpy.mean(event_frequencies, axis=0, keepdims=1),
			axis=0, keepdims=1),
		axis=0, keepdims=1)		#mads = numpy.mean(event_frequencies-numpy.mean(event_frequencies, axis=0), axis=0)
		# mads: dict of event: MAD
		mads = {e:mads[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		mads = {e:mads[e] for e in sorted(mads.keys(), key=lambda item:mads[item])}
		# sort by MAD value.
		if self.Informative == "most":
			self._mads = list(mads.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._mads = list(mads.keys())[:self.numEvents]
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
				print(d.eventSet)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._mads]

	def displayName():
		return "Mean Absolute Deviation"
	def displayDescription():
		return "Analyzes N events with the lowest or highest Mean Absolute Deviation. MAD = sum(|xi-mean|)/n"

class CoefficientOfVariation(EventCulling):
	"""Standard deviation over mean"""
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 1, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		covs = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		covs = numpy.std(event_frequencies, axis=0, keepdims=1) / numpy.mean(event_frequencies, axis=0, keepdims=1)

		# covs: dict of event: CoV
		covs = {e:covs[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		covs = {e:covs[e] for e in sorted(covs.keys(), key=lambda item:covs[item])}
		if self.Informative == "most":
			self._covs = list(covs.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._covs = list(covs.keys())[:self.numEvents]
		#print(self._covs)
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
				#print(docs[i].eventSet)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._covs]

	def displayName():
		return "Coefficient of Variation"

	def displayDescription():
		return "Analyzes N events with the lowest or highest Coefficient of Variation, given as stdev/mean."


class IndexOfDispersion(EventCulling):
	"""Variance over mean"""
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		iods = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		iods = numpy.var(event_frequencies, axis=0, keepdims=1)\
			/ numpy.mean(event_frequencies, axis=0, keepdims=1)

		# iods: dict of event: IoD
		iods = {e:iods[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		iods = {e:iods[e] for e in sorted(iods.keys(), key=lambda item:iods[item])}
		# sort by IoD value.
		if self.Informative == "most":
			self._iods = list(iods.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._iods = list(iods.keys())[:self.numEvents]
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
				print(d.eventSet)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._iods]

	def displayName():
		return "Index of Dispersion"

	def displayDescription():
		return "Analyzes N events with the lowest or highest Index of Dispersion, which is given by stdev^2/mean."

class StandardDeviation(EventCulling):
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		stds = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		stds = numpy.std(event_frequencies, axis=0)

		# iods: dict of event: IoD
		stds = {e:stds[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		stds = {e:stds[e] for e in sorted(stds.keys(), key=lambda item:stds[item])}
		# sort by IoD value.
		if self.Informative == "most":
			self._stds = list(stds.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._stds = list(stds.keys())[:self.numEvents]
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._stds]

	def displayName():
		return "Standard Deviation"

	def displayDescription():
		return "Analyzes N events with the lowest or highest Standard Deviation."

class RangeCuller(EventCulling):
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		rang = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		rang = numpy.max(event_frequencies, axis=0) - numpy.min(event_frequencies, axis=0)

		# iods: dict of event: IoD
		rang = {e:rang[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		rang = {e:rang[e] for e in sorted(rang.keys(), key=lambda item:rang[item])}
		# sort by IoD value.
		if self.Informative == "most":
			self._rang = list(rang.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._rang = list(rang.keys())[:self.numEvents]
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._rang]

	def displayName():
		return "Range Culler"

	def displayDescription():
		return "Analyzes N events with the lowest or highest range of frequencies."

class Variance(EventCulling):
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		var = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
        
		var = numpy.var(event_frequencies, axis=0)

		# iods: dict of event: IoD
		var = {e:var[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		var = {e:var[e] for e in sorted(var.keys(), key=lambda item:var[item])}
		# sort by IoD value.
		if self.Informative == "most":
			self._var = list(var.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._var = list(var.keys())[:self.numEvents]
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._var]

	def displayName():
		return "Variance"

	def displayDescription():
		return "Analyzes N events with the lowest or highest Variance."

class WeightedVariance(EventCulling):
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]
    

	def process(self, docs, pipe=None):
		wvar = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		relative_freq = event_frequencies / len(event_frequencies)
		wvar = numpy.sum(relative_freq*(event_frequencies - numpy.mean(relative_freq*event_frequencies,
			axis=0, keepdims=1)),
		axis=0, keepdims=1)

		# iods: dict of event: IoD
		wvar = {e:wvar[i] for i, e in enumerate(event_names)}
		# sort the dictionary
		wvar = {e:wvar[e] for e in sorted(wvar.keys(), key=lambda item:wvar[item])}
		# sort by IoD value.
		if self.Informative == "most":
			self._wvar = list(wvar.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._wvar = list(wvar.keys())[:self.numEvents]
		print(self._wvar)
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._wvar]

	def displayName():
		return "Weighted Variance"

	def displayDescription():
		return "Analyzes N events with the lowest or highest Variance weighted by relative frequency."




"""
class InformationGain(EventCulling):
	_default_multiprocessing = True
	_variable_options = {
		"numEvents": {"options": range(1, 201), "default": 49, "type": "Slider"},
        "Informative": {"options": ["most", "least"], "default": 0, "type": "OptionMenu"}
        }
	numEvents = _variable_options["numEvents"]["options"][_variable_options["numEvents"]["default"]]
	Informative = _variable_options["Informative"]["options"][_variable_options["Informative"]["default"]]

	def process(self, docs, pipe=None):
		igs = dict()
		# get 2D array of events, where D1 is documents; D2 is the feature vector. (auto-filled zeros)
		cv = CountVectorizer(analyzer=lambda t:t)
		event_frequencies = cv.fit_transform([d.eventSet for d in docs]).toarray()
		event_names = cv.get_feature_names_out()
		relative_freq = [[event/len(event_frequencies) for event in event_frequency]for event_frequency in event_frequencies]
		for (event, rowAbs, rowRel) in zip(event_names, event_frequencies, relative_freq):
            #Calculation of the information gain of events. This is the only issue with the code.
			igs[event] = numpy.log(numpy.prod([scipy.special.factorial(i) for i in rowAbs], axis=0)/(scipy.special.factorial(numpy.sum(rowAbs))*(numpy.prod([numpy.power(rowRel[i], rowAbs[i]) for i in range(len(rowAbs))], axis=0))))
		# sort by IG value.
		if self.Informative == "most":
			self._igs = list(igs.keys())[-self.numEvents:]
		elif self.Informative == "least":
			self._igs = list(igs.keys())[:self.numEvents]
		print(self._igs)
		if self._default_multiprocessing:
			with Pool(cpu_count()-1) as pool:
				new_event_sets = pool.map(self.process_single, docs)
			for i, v in enumerate(new_event_sets):
				docs[i].setEventSet(v, append=False)
		else:
			for d_i, d in enumerate(docs):
				if pipe is not None: pipe.send(d_i/len(docs))
				new_events = self.process_single(d)
				d.setEventSet(new_events, append=False)
				print(d.eventSet)
		return

	def process_single(self, doc):
		return [e for e in doc.eventSet if e in self._igs]

	def displayName():
		return "Information Gain"

	def displayDescription():
		return "Select the n most or least informative events accross all documents, given by log(sum(x!)/(sum(x)!(prod(Pi^x))))"
"""