from generics.DistanceFunction import DistanceFunction
import numpy as np

class CosineDistance(DistanceFunction):
	def distance(self, unknown, known:np.ndarray):
		"""Compute distance using numpy"""
		unknown_magnitude = np.sqrt(np.sum(np.square(unknown), axis=1, keepdims=1))
		known_magnitude = np.sqrt(np.sum(np.square(known), axis=1, keepdims=1))
		doc_by_author_distance = 1-np.divide(np.matmul(unknown, known.transpose()), np.matmul(unknown_magnitude, known_magnitude.transpose()))
		return doc_by_author_distance

	def displayDescription():
		return "Computes cosine distance/similarity"

	def displayName():
		return "Cosine Distance"


class HistogramDistance(DistanceFunction):
	square_root = 0
	_variable_options = {
		"square_root": {"options": [0, 1], "default": 0, "type": "Tick", "displayed_name": "Compute square root"}
	}
	def distance(self, unknown, known:np.ndarray):
		"""Compute distance using numpy"""
		doc_by_author = np.sum(np.square(unknown[:,np.newaxis] - known), axis=2, keepdims=0)
		if self.square_root: doc_by_author = np.sqrt(doc_by_author)
		return doc_by_author

	def displayDescription():
		return "Computes Euclidean/Histogram distance"

	def displayName():
		return "Histogram Distance"

class LNorms(DistanceFunction):
	p = "1"
	compute_root = 0
	_variable_options = {
		"p": {"options": ["1/"+str(x) for x in list(range(10, 1, -1))] + [str(x) for x in list(range(1, 11))], "default": 9},
		"compute_root": {"options": [0, 1], "default": 0, "type": "Tick", "displayed_name": "Compute root"}
	}

	def distance(self, unknown, known: np.ndarray):
		power = 1/int(self.p.split("/")[-1]) if "/" in self.p else int(self.p)
		doc_by_author = np.sum(np.power(unknown[:,np.newaxis] - known, power), axis=2, keepdims=0)
		if self.compute_root: doc_by_author = np.power(doc_by_author, 1/power)
		return doc_by_author

	def displayDescription():
		return "Computes L-Norms. 2-norm is equivalent to histogram/Euclidean distance"

	def displayName():
		return "L-Norms"

# class LebesgueDistance(DistanceFunction):
# 	test = 0
# 	_variable_options = {
# 		"test": {"options": [0, 2, 5], "default": 0, "displayed_name": "TEST LMAO"}
# 	}

# 	def distance(self, unknown, known: np.ndarray):
# 		pass

# 	def displayName():
# 		return "Lebesgue Distance"

# 	def displayDescription():
# 		return "Computes Euclidean/Histogram distance"

# class BhattacharyyaDistance(DistanceFunction):
# 	def distance(self, unknown:np.array, known:np.array):
# 		"""Convert and assign to Documents.numbers"""
# 		distance = np.matmul(np.sqrt(unknown), np.sqrt(known).transpose())
# 		distance = -1*np.log(distance)
# 		return distance

# 	def displayDescription():
# 		return "Computes Bhattacharyya distance"

# 	def displayName():
# 		return "Bhattacharyya Distance"