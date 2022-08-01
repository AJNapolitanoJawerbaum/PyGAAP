from generics.AnalysisMethod import *
# pn is backend.PrepareNumbers, already imported from generics.AnalysisMethod
from sklearn.svm import LinearSVC

class SVM_from_sklearn(AnalysisMethod):
	penalty = "L2"
	opt = "dual"
	tol = 0.0001
	reg_strength = 1
	iterations = 1000
	_NoDistanceFunction_ = True

	_model = None

	_variable_options = {
		"iterations": {"options": [10, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000], "type": "OptionMenu", "default": 4, "displayed_name": "Iterations"},
		"tol": {"options": [0.00001, 0.00002, 0.00005, 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05],
			"type": "OptionMenu", "default": 3, "displayed_name": "Stopping Tolerance"},
		"penalty": {"options": ["L1", "L2"], "type": "OptionMenu", "default": 1, "displayed_name": "Penalty type"},
		"reg_strength": {"options": list(range(1, 11)), "type": "OptionMenu", "default": 0, "displayed_name": "Regularization Strength"},
		"opt": {"options": ["primal", "dual"], "type": "OptionMenu", "default": 1, "displayed_name": "Optimization Problem"},
	}
	_display_to_input = {"penalty": {"L1": "l1", "L2": "l2"}, "dual": {"dual": True, "primal": False}}
	
	def after_init(self, **options):
		...

	def train(self, train, train_data):
		train_labels, self._labels_to_categories =\
			pn.auth_list_to_labels([d.author for d in train])

		train_labels = train_labels.flatten() # sklearn's svm takes flattened labels array.

		if train_data is None:
			train_data = self.get_train_data(train)
		self._model = LinearSVC(
			max_iter=self.iterations, tol=self.tol, penalty=self._display_to_input["penalty"][self.penalty],
			C=1/self.reg_strength, dual=self._display_to_input["dual"][self.opt]
		)
		self._model.fit(train_data, train_labels)
		return

	def analyze(self, test, test_data):
		if test_data is None:
			test_data = self.get_test_data(test)
		scores = -self._model.decision_function(test_data)
		if len(scores.shape) == 1:
			# in case of binary classification, sklearn returns
			# a 1D array for scores. need to re-format to 2D.
			scores = np.array((scores, 1-scores)).transpose()
		results = self.get_results_dict_from_matrix(scores)
		return results

	def displayName():
		return "Linear SVM (sklearn)"

	def displayDescription():
		return """Support vector machine implemented in Scikit-learn. (sklearn.svm.LinearSVC).
		Parameters are set to the default from sklearn.
		Parameters:
		\tIterations: number of iterations to run.
		\tStopping tolerance: Tolerance for the stopping criteria.
		\tPenalty: Specifies the norm used in the penalization.
		\tRegularization Strength: Strength of constraints on size of parameters.
		\tOptimization Problem: which problem to solve. Use "primal" if the texts are large in number but short in content, or,
		number of samples > number of features.\n
		To see more details, go to https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html.
		"""