from generics.DistanceFunction import *
import numpy as np

class CosineDistance(DistanceFunction):
	def distance(self, unknown, known:np.ndarray):
		"""Compute distance using numpy"""
		unknown_magnitude = np.sqrt(np.sum(np.square(unknown), axis=1, keepdims=1))
		known_magnitude = np.sqrt(np.sum(np.square(known), axis=1, keepdims=1))
		doc_by_author_distance = 1-np.divide(np.matmul(unknown, known.transpose()), np.matmul(unknown_magnitude, known_magnitude.transpose()))
		return doc_by_author_distance

	def displayDescription():
		return "Computes cosine distance/similarity\n[UNVERIFIED]"

	def displayName():
		return "Cosine Distance"


class HistogramDistance(DistanceFunction):
	def distance(self, unknown, known:np.ndarray):
		"""Compute distance using numpy"""
		doc_by_author = np.sqrt(np.sum(np.square(unknown[:,np.newaxis] - known), axis=2, keepdims=0))
		return doc_by_author

	def displayDescription():
		return "Computes Euclidean/Histogram distance\n[UNVERIFIED]"

	def displayName():
		return "Histogram Distance"

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