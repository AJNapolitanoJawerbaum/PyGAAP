from sys import path as sys_path
from os import getcwd
from pathlib import Path
sys_path.append(getcwd())

from backend import CSVIO
from backend import API
from backend.Document import Document
from backend.GUI import GUI_run_experiment

api = API.API("")
corpus = CSVIO.readCorpusCSV("./resources/aaac/problemC/loadC.csv")

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

mod_names = {
    "canonicizers_names": [],
    "event_drivers_names": ["Character NGrams"],
    "event_cullers_names": [],
    "number_converters_names": ["Frequency"],
    "am_df_names": [["Centroid Driver", "Histogram Distance"]]
}
api.modulesInUse["EventDrivers"].append(api.eventDrivers["Character NGrams"]())
api.modulesInUse["NumberConverters"].append(api.numberConverters["Frequency"]())
api.modulesInUse["AnalysisMethods"].append(api.analysisMethods["Centroid Driver"]())
api.modulesInUse["DistanceFunctions"].append(api.distanceFunctions["Histogram Distance"]())


exp = GUI_run_experiment.Experiment(api, mod_names)
results = exp.run_experiment(return_results=True)

print(results)