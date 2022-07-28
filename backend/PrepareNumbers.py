
# author: @ Michael Fang

"""
Utils for frequently used operations involving NumPy & SciPy

e.g.
doc1.author = a1, doc1.numbers: {'a': 3, 'b': 5},
doc2.author = a2, doc2.numbers: {'a': 4, 'c': 12}:

-->
 data:        a  b  c      labels:
doc1 >>     [[3, 5, 0],     [[a1],
doc2 >>      [4, 0, 12]]     [a2]]
"""


import numpy as np
import pandas as pd
from scipy.sparse import csr_array, coo_array, _arrays



def dicts_to_array(events: list, **options) -> np.ndarray:
	"""
	Converts list of dictionaries to a single NumPy array.\n
	Each dict is a row; each key in dict is a column.\n
	If dicts have different sets of keys, it expands the columns
	to include all keys in all documents.\n
	i.e. doc1 {'a': 1, 'b': 2}, doc2 {'a': 3, 'c': 4} ->\n
	[1, 2, 0]\n
	[3, 0, 4]\n
	Options: `bool sort_keys`: whether to sort dict keys (usually used for debugging only.)
	"""
	sorted = options.get("sort_keys", False)
	cols = list(set([dict_keys for dic in events for dict_keys in list(dic.keys())]))
	if sorted: cols.sort()
	df = pd.DataFrame(events).fillna(0)[cols].values

	return np.array(df)


def auth_list_to_labels(auth_list, **options):
	"""
	Convert list of authors to training data and labels.
	Training data extracted from Document.eventSet
	The labels are numerical.
	Returns train data in np.ndarray, labals in np.ndarray,
	and a dict to retrieve categories from the numerical labels.
	"""
	labels_to_categories = dict() # retrieve original category names from numerical labels.
	categories_to_labels = dict()
	# ^^ keeps track of which categories have been assigned numerical labels
	labels = np.zeros((len(auth_list), 1), dtype=np.intc)
	category_alias = 0
	for auth_ind in range(len(auth_list)):
		auth = auth_list[auth_ind]
		assert auth != "", "Expected author to be non-empty (i.e. training data)"
		numerical_label = categories_to_labels.get(auth)
		if numerical_label == None:
			# no numerical assigned yet
			categories_to_labels[auth] = category_alias
			labels_to_categories[category_alias] = auth
			numerical_label = category_alias
			category_alias += 1
		
		labels[auth_ind][0] = numerical_label
		
	return labels, labels_to_categories
	

def find_mean_per_author(data, labels):
	"""Finds the mean per category. Equivalent to finding mean author histogram"""
	label_set = np.unique(labels[:,0])
	means = np.zeros((label_set.shape[0], data.shape[1]))
	row = 0
	
	for label in label_set:
		this_category = data[np.where(labels[:,0] == label)]
		if type(data) == np.ndarray:
			this_category = np.mean(this_category, axis=0, keepdims=1)
		elif type(data) == _arrays.csr_array:
			this_category = this_category.mean(axis=0)
		means[row]=this_category
		row += 1
	return means, label_set.reshape((means.shape[0],1))
