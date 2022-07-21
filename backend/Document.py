from pathlib import Path

class Document:
	'''Document object'''
	author = ""
	title = ""
	text = ""
	eventSet = []
	filepath = ""
	
	def __init__(self, author, title, text, filepath):
		'''Document object constructor.'''
		self.author = author
		self.title = title
		self.text = text
		self.filepath = filepath
		self.eventSet = []
		
	def setEventSet(self, eventSet, **options):
		'''Sets the eventSet list value.'''
		append = options.get("append", False)
		if not append:
			self.eventSet = eventSet
		else:
			self.eventSet += eventSet
	
	def read_self(self, encoding=None):
		f = open(Path(self.filepath), "r")
		if encoding == None:
			try:
				self.text = f.read()
			except UnicodeError:
				try: self.text = f.read(encoding="UTF-8")
				except UnicodeError: self.text = f.read(encoding="ISO-8859-15")
		else: self.text = f.read(encoding=encoding)
		f.close()
		return self.text
	
	def __repr__(self):
		return '<Auth: "%s", Title: "%s", Text sample: |%s|, Event sample: %s, Path: %s>' % \
			(str(self.author), str(self.title), str(self.text[:10]), str(self.eventSet[:10]), str(self.filepath))
