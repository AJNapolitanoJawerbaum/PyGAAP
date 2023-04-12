from sys import path as sys_path
from os import getcwd
from pathlib import Path

#p="/".join(getcwd().split("/")[:-1])
sys_path.append(getcwd())

from generics import AnalysisMethod as am
from generics import Embedding as nc
from generics.modules import *
from generics.modules.nc_0 import Frequency
from generics.modules.df_0 import CosineDistance
from util import generate_random as gr
from backend import PrepareNumbers as pn

def test_analysis_1():
    centroid = am.CentroidDriver2()
    freq = Frequency()
    freq.normalization = "zero-max scaling"
    doc_list = gr.rand_docs(15, 5, 1)
    #[print(d) for d in doc_list]

    test_doc_list = gr.rand_docs(3, 3, 1) # generate unknown docs
    train_test_data = freq.convert(doc_list+test_doc_list) # convert known data to numbers

    train_data = train_test_data[:len(doc_list)]
    test_data = train_test_data[len(doc_list):]

    centroid.train(doc_list, train_data) # compute centroids on known
    cosdist = CosineDistance()  # initiate distance function
    centroid.setDistanceFunction(cosdist)   # set distance function

    final_result = centroid.analyze(test_doc_list, test_data) # analyze unknown all at once
    print(final_result)

test_analysis_1()