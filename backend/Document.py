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
		self.canonicized = extras.get("canonicized", None)
		self.numbers = extras.get("numbers", None)
		self.eventSet = extras.get("eventSet", list())

		self.author = extras.get("author", self.author)
		self.title = extras.get("title", self.title)
		self.text = extras.get('text', self.text)
		self.filepath = extras.get('filepath', self.filepath)
		
	def setEventSet(self, eventSet, **options):
		'''Sets the eventSet list value.'''
		append = options.get("append", True)
		if not append:
			self.eventSet = eventSet
		else:
			self.eventSet += eventSet
	
	def read_self(self, encoding=None):
		try:
			self.text = Path(self.filepath).read_text()
		except UnicodeError:
			try:
				self.text = Path(self.filepath).read_text(encoding="UTF-8")
			except UnicodeError:
				self.text = Path(self.filepath).read_text(encoding="ISO-8859-15")
		self.text += "\n"
		return self.text
	
	def __repr__(self):
		return '<Auth: "%s", Title: "%s", Text sample: |%s|, Event sample: %s, Path: %s>' % \
			(str(self.author), str(self.title), str(self.text[:10]), str(self.eventSet)[:10]+"...", str(self.filepath))

	def __eq__(self, other):
		try:
			for att in self.__dict__:
				if att[0] != "_" and self.__dict__[att] != other.__dict__[att]:
					return False
		except AttributeError: return False
		return True

	def is_same_doc(self, other):
		if self.author == other.author and self.title == other.title and self.filepath == other.filepath:
			return True
		else: return False
		