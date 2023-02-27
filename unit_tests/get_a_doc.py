from random import sample
from os import listdir as ls


def get_doc_list():
	doc_list = []
	for problem in ls("./resources/aaac/"):
		doc_list += ["./resources/aaac/%s/%s"%(problem, s) for s in ls("./resources/aaac/"+problem+"/")]
	return doc_list

def get_doc(how_many=1):
	doc_list = get_doc_list()
	r = sample(doc_list, how_many)
	if len(r) == 1: return r[0]
	else: return r

def get_long():
	r = "./resources/aaac/problemI/" + sample(ls("./resources/aaac/problemI/"), 1)[0]
	return r