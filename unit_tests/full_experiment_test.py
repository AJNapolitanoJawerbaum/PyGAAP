from sys import path as sys_path
from os import getcwd
from pathlib import Path
sys_path.append(getcwd())

from backend import CSVIO
from backend import API
from backend.Document import Document
from backend import run_experiment

print("load API...", end="")
api = API.API("")
corpus = CSVIO.readCorpusCSV("./resources/aaac/problemA/loadA.csv")
print("done. Loading docs...", end="")
for doc in corpus:
    if doc[0] == "":
        api.unknown_docs.append(Document(title=doc[2], filepath=doc[1]))
corpus = [x for x in corpus if x[0] != ""]

known_dict = dict()
for d in corpus:
    known_dict[d[0]] = known_dict.get(d[0], []) + [d[1]]

known_dict = [[x, known_dict[x]] for x in known_dict]

api.known_authors = known_dict
del known_dict, corpus
print("done. starting exp.")

# add modules here
api.modulesInUse["EventDrivers"].append(api.eventDrivers["Character NGrams"]())
#api.modulesInUse["EventCulling"].append(api.eventCulling["Coefficient of Variation"]())
api.modulesInUse["Embeddings"].append(api.embeddings["Frequency"]())
api.modulesInUse["AnalysisMethods"].append(api.analysisMethods["Centroid Driver"]())
api.modulesInUse["DistanceFunctions"].append(api.distanceFunctions["Histogram Distance"]())

# set module parameters here
api.modulesInUse["EventDrivers"][0].n = 1
api.modulesInUse["Embeddings"][0].normalization = "Per-document token count"
#api.modulesInUse["Embeddings"][-1].convert_from = "features"
#api.modulesInUse["Embeddings"][-1].long_text_method = "average every 64"

exp = run_experiment.Experiment(api)
results = exp.run_experiment(return_results=1, verbose=1)

print(results["results_text"])
print(results["message"])