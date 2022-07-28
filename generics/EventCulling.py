from abc import ABC, abstractmethod
from importlib import import_module


# An abstract Event Culling class.
class EventCulling(ABC):

	def __init__(self):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except:
			self._variable_options = dict()

	@abstractmethod
	def process(self, eventSet):
		'''To be determined'''
		pass
		
	@abstractmethod
	def displayName():
		'''Returns the display name for the given event culler.'''
		pass

	@abstractmethod
	def displayDescription():
		'''Returns the display description for the event culler.'''


class N_Occurrences(EventCulling):
	_variable_options = {
		"Mode": {"options": ["Cull more freq.", "Cull less freq."], "type": "OptionMenu", "default": 0},
		"Frequency": {"options": list(range(1, 10)), "default": 0, "type": "OptionMenu", "default": 0},
	}

	Frequency = _variable_options["Frequency"]["options"][_variable_options["Frequency"]["default"]]
	Mode = _variable_options["Mode"]["options"][_variable_options["Mode"]["default"]]
	
	def process(self, eventSet: list):
		freq = dict()
		for e in eventSet:
			if freq.get(e) == None: freq[e] = 1
			else: freq[e] += 1
		if self.Mode == "Cull more freq.":
			new_events = [ev for ev in eventSet if (freq.get(ev)!=None and freq.get(ev) <= self.Frequency)]
		if self.Mode == "Cull less freq.":
			new_events = [ev for ev in eventSet if (freq.get(ev)!=None and freq.get(ev) >= self.Frequency)]
		return new_events

	def displayName():
		return "N occurrences"

	def displayDescription():
		return "Remove features that are encountered N or fewer/more times."