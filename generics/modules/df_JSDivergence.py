from generics.DistanceFunction import DistanceFunction
import numpy as np


class JSDistance(DistanceFunction):
	def distance(self, unknown:np.ndarray, known:np.ndarray):
		"""Compute distance using numpy"""
		unknown_split = unknown[:,np.newaxis]
		reference_distribution = (unknown_split + known) / 2
		# references where for each unknown item there is a matrix
		# of comparisons with all the known items.

		single_term_kl_unknown_to_reference = \
			np.where(unknown_split==0, 0,
			np.where(reference_distribution==0, 0,
			unknown_split * np.log2(unknown_split/reference_distribution)))
		kl_unknown_to_reference = np.sum(single_term_kl_unknown_to_reference, axis=2)

		single_term_kl_known_to_reference = \
			np.where(known==0, 0,
			np.where(reference_distribution==0, 0,
			known * np.log2(known/reference_distribution)))
		kl_known_to_reference = np.sum(single_term_kl_known_to_reference, axis=2)

		js = np.sqrt(kl_unknown_to_reference + kl_known_to_reference)/2
		return js

	def displayDescription():
		return "Computes Jensen-Shannon distance, the square root of Jensen-Shannon divergence."

	def displayName():
		return "Jensen-Shannon Distance"
