# PyGAAP User Manual
The Python graphical authorship attribution program is a text classification tool in Python and a port of JGAAP, the original java version. It follows the typical steps seen in a text classification task: from pre-processing, feature extraction, and feature culling to text embedding and analysis.

 - Please see the developer manual if you would like to extend PyGAAP.

## Ten-second GUI demo
1. Launch PyGAAP,
2. Click on ```Files``` $\rightarrow$ ```AAAC Problems``` $\rightarrow$ ```Problem A```
3. Switch to the ```Event drivers``` tab, click on ```Character NGrams```, then ```Add```
4. Switch to the ```Embeddings``` tab and click on ```Frequency```, then ```Add```
5. Switch to the ```Analysis Methods``` tab and click on ```Linear SVM (sklearn)```, then ```Add```.
6. Finally, switch to ```Review & Process``` tab, press ```Process```, and wait for the results!

# The graphical interface
## Loading document(s)
### Unknown documents (the testing set)
### Known documents (the training set)

## Modules
### Alternative names
The module types in PyGAAP have alternative names one may have seen in academic papers or other machine learning programs. Here are some of the names one may encounter.
- ```Canonicizers```: Pre-processing; Text normalization.
- ```Event Drivers```: Feature (set) extraction, Characteristics extraction, "Write-print" (a particular feature extraction method).
- ```Event Culling```: Feature (set) culling/filtering.
- ```Embeddings```: Feature embedding
- ```Analysis Methods```: Classifiers, Algorithms.
- ```Distance Functions```: Distances, Metrics.
### Add/remove modules
### Module parameters
### Search modules

# The command line
## Corpus and experiment CSVs
### Creating a corpus csv
### Creating an experiment csv
parameters
### Loading a JGAAP experiment csv
PyGAAP is cross-compatible with JGAAP experiment csv format. Simply run the CLI as if you'd run a PyGAAP csv. Caution that since JGAAP's exp. csv format doesn't specify an embedding, the default will always be ```Frequency```.
### Convert a JGAAP expriment csv to the PyGAAP format
## Running the experiment