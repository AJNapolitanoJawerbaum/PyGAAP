from sys import path as sys_path
from os import getcwd
from pathlib import Path
sys_path.append(getcwd())

from copy import copy as shallowcopy

from backend import CSVIO
from backend import API
from backend.Document import Document
from generics.modules.nc_0 import Frequency
from generics.EventDriver import CharacterNGramEventDriver as ngram
from generics.AnalysisMethod import CentroidDriver as centroid
from generics.modules.am_sklearn import SVM_from_sklearn as svm
from generics.modules.df_0 import HistogramDistance as euclidean

corpus = CSVIO.readCorpusCSV("./resources/aaac/problemI/loadI.csv")

unknown_docs = []
api_known_auths = []

for doc in corpus:
	if doc[0] == "":
		unknown_docs.append(Document(title=doc[2], filepath=doc[1]))
corpus = [x for x in corpus if x[0] != ""]
known_dict = dict()
for d in corpus:
	known_dict[d[0]] = known_dict.get(d[0], []) + [d[1]]
known_dict = [[x, known_dict[x]] for x in known_dict]

known_docs = []
for author in known_dict:
	for authorDoc in author[1]:
		known_docs.append(Document(author[0],
			authorDoc.split("/")[-1],
			"", authorDoc))

# make copies for use in processing.
# This is much faster than deepcopying after reading the files,
# especially for long files.


for d in known_docs: d.text = CSVIO.readDocument(d.filepath)
for d in unknown_docs: d.text = CSVIO.readDocument(d.filepath)

ed = ngram()
for d in known_docs: d.setEventSet(ed.createEventSet(d.text), append=1)
for d in unknown_docs: d.setEventSet(ed.createEventSet(d.text), append=1)


nc = Frequency()

all_data = nc.convert(known_docs + unknown_docs)
known_docs_numbers_aggregate = all_data[:len(known_docs)]
unknown_docs_numbers_aggregate = all_data[len(known_docs):]
del all_data

am = svm()
df = euclidean()

am.setDistanceFunction(df)
am.train(known_docs, known_docs_numbers_aggregate)

results = am.analyze(unknown_docs, unknown_docs_numbers_aggregate)

print(results)


