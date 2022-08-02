from pathlib import Path

class Document:
	'''Document object'''
	author = "" # string
	title = "" # string
	text = "" # string
	eventSet = [] # list of strings
	numbers = None # np.ndarray. If 1D, must be 1D array, 2D-> 2D. (no extra dimensions)
	filepath = "" # string
	
	def __init__(self, author="", title="", text="", filepath="", **extras):
		'''
		Document object constructor. specify author, title, text, and filepath
		in this order or as keyword arguments.
		'''
		self.author = author
		self.title = title
		self.text = text
		self.filepath = filepath
		self.numbers = extras.get("numbers", None)
		self.eventSet = extras.get("eventSet", list())

		self.author = extras.get("author", self.author)
		self.title = extras.get("title", self.title)
		self.text = extras.get('text', self.text)
		self.filepath = extras.get('filepath', self.filepath)
		
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
			(str(self.author), str(self.title), str(self.text[:10]), str(self.eventSet)[:10]+"...", str(self.filepath))
