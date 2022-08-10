from abc import ABC, abstractmethod
from importlib import import_module


# An abstract Event Culling class.
class EventCulling(ABC):

	def __init__(self, **options):
		try:
			for variable in self._variable_options:
				setattr(self, variable, self._variable_options[variable]["options"][self._variable_options[variable]["default"]])
		except AttributeError:
			self._variable_options = dict()

		try: self.after_init(**options)
		except (AttributeError, NameError): pass

	def after_init(self, **options):
		pass

	def validate_parameter(self, param_name: str, param_value):
		"""validating parameter expects param_value to already been correctly typed"""
		if param_name not in self._variable_options:
			raise NameError("Unknown parameter in module")
		validator = self._variable_options[param_name].get("validator")
		if validator != None:
			val_result = validator(param_value)
			if not val_result: raise ValueError("Module parameter out of range")
		elif param_value not in self._variable_options[param_name]["options"]:
			raise ValueError("Module parameter out of range")
		return

	def process(self, docs, pipe):
		"""Process all docs"""
		for d_i in range(l:=len(docs)):
			if pipe is not None: pipe.send(100*d_i/l)
			d = docs[d_i]
			new_events = self.process_single(d.eventSet)
			d.setEventSet(new_events)
		return
			
		
	def process_single(self, eventSet):
		"""Process a single document"""
		
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
	
	def process_single(self, eventSet: list):
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