from generics.module import AnalysisMethod
# pn is backend.PrepareNumbers, already imported from generics.AnalysisMethod
from sklearn.svm import LinearSVC, SVC
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import numpy as np

class Linear_SVM_sklearn(AnalysisMethod):
	penalty = "L2"
	opt = "dual"
	tol = 0.0001
	reg_strength = 1
	iterations = 1000
	_NoDistanceFunction_ = True

	_model = None

	_variable_options = {
		"iterations": {"options": [10, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000],
			"type": "OptionMenu", "default": -1, "displayed_name": "Iterations",
			"validator": (lambda x: x in range(2, 500001))},
		"tol": {"options": [0.00001, 0.00002, 0.00005, 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05],
			"type": "OptionMenu", "default": 3, "displayed_name": "Stopping Tolerance",
			"validator": (lambda x: (x > 0.000001 and x < 0.1))},
		"penalty": {"options": ["L1", "L2"], "type": "OptionMenu", "default": 1, "displayed_name": "Penalty type"},
		"reg_strength": {"options": range(1, 11), "type": "Slider", "default": 0, "displayed_name": "Regularization Strength"},
		"opt": {"options": ["primal", "dual"], "type": "OptionMenu", "default": 1, "displayed_name": "Optimization Problem"},
	}
	_display_to_input = {"penalty": {"L1": "l1", "L2": "l2"}, "dual": {"dual": True, "primal": False}}
	
	def after_init(self, **options):
		...

	def train(self, train, train_data, **options):
		"""Create model in train() because after this starts the parameters won't change."""
		train_data, train_labels = self.get_train_data_and_labels(train, train_data)

		train_labels = train_labels.flatten() # sklearn's svm takes flattened labels array.

		self._model = LinearSVC(
			max_iter=self.iterations, tol=self.tol, penalty=self._display_to_input["penalty"][self.penalty],
			C=1/self.reg_strength, dual=self._display_to_input["dual"][self.opt]
		)
		self._model.fit(train_data, train_labels)
		return

	def process(self, docs, pipe=None, **options):
		self.train([d for d in docs if d.author != ""], options.get("known_numbers"))
		test_data = self.get_test_data(docs, options)
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

class MLP_sklearn(AnalysisMethod):

	hidden_width = 100
	depth = 1
	activation = "ReLU"
	learn_rate_init = 0.001
	learn_rate_mode = "constant"
	iterations = 200
	tol = 0.0001
	validation_fraction = 0.1

	_variable_options = {
		"hidden_width": {"options": list(range(2,10))+[10,20,30,40,50,75,100,200,300,400,500,750,1000],"default": 14,
			"displayed_name": "Hidden layers width", "validator": (lambda x: (x > 1 and x < 5001))},
		"depth": {"options": list(range(1, 10))+[10,15,20,25,30,35,40,45,50,100], "default":0, "displayed_name": "Network depth",
			"validator": (lambda x: (x > 0 and x < 1001))},
		"activation": {"options": ["ReLU", "tanh", "Logistic", "Identity"], "default": 0, "displayed_name": "Activation function"},
		"learn_rate_init": {"options": [0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2], "default": 3,
			"displayed_name": "Initial learn rate", "validator": (lambda x: (x > 0.00001 and x <= 1))},
		"learn_rate_mode": {"options": ["Constant", "Inverse Scaling", "Adaptive"], "default": 0, "displayed_name": "Learn rate mode"},
		"iterations": {"options": [10, 50, 100, 200, 300, 400, 500, 750, 1000, 2500, 5000, 7500, 10000], "default": -1,
			"displayed_name": "Maximum iterations", "validator": (lambda x: (x > 1 and x < 100001))},
		"tol": {"options": [0.00001, 0.00002, 0.00005, 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05],
			"type": "OptionMenu", "default": 3, "displayed_name": "Stopping Tolerance", "validator": (lambda x: (x >= 0.000001 and x <=0.1))},
		"validation_fraction": {"options": [0.05, 0.45], "type": "Slider", "resolution": 0.05, "default": 1, "displayed_name": "Fraction used for validation",
			"validator": (lambda x: (x > 0.01 and x < 0.5))}
	}

	_display_to_input = {
		"learn_rate_mode": {"Constant": "constant", "Inverse Scaling": "invscaling", "Adaptive": "adaptive"}
	}

	_NoDistanceFunction_ = True

	def train(self, train, train_data):
		train_data, train_labels = self.get_train_data_and_labels(train, train_data)
		train_labels = train_labels.flatten()
		self._model = MLPClassifier(
			hidden_layer_sizes=(self.hidden_width,)*self.depth,
			activation=self.activation.lower(),
			learning_rate_init=self.learn_rate_init,
			learning_rate=self._display_to_input["learn_rate_mode"][self.learn_rate_mode],
			max_iter=self.iterations,
			tol=self.tol,
			validation_fraction=self.validation_fraction
		)

		self._model.fit(train_data, train_labels)
		return

	
	def process(self, docs, Pipe=None, **options):
		self.train([d for d in docs if d.author != ""], options.get("known_numbers"))
		test_data = self.get_test_data(docs, options)
		results = self._model.predict_proba(test_data)
		if len(results.shape) == 1:
			results = np.array((results, 1-results)).transpose()

		results = self.get_results_dict_from_matrix(1-results)
		return results


	def displayName():
		return "Multi-layer perceptron (sklearn)"

	def displayDescription():
		return "[multi-process]\nMulti-layer perceptron/neural network implemented in scikit-learn."


class Naive_bayes_sklearn(AnalysisMethod):

	_NoDistanceFunction_ = True

	alpha = 1
	_variable_options = {"alpha":
		{"options": [0, 0.2, 0.4, 0.6, 0.8, 1], "default": 5,
			"displayed_name": "Adaptive smoothing", "validator": (lambda x: (x >= 0 and x <= 2))}
	}

	def train(self, train, train_data=None, **options):
		train_data, train_labels = self.get_train_data_and_labels(train, train_data)
		self._model = MultinomialNB(alpha = self.alpha)
		train_labels = train_labels.flatten()
		self._model.fit(train_data, train_labels)
		return

	def process(self, docs, Pipe=None, **options):
		self.train([d for d in docs if d.author != ""], options.get("known_numbers"))
		test_data = self.get_test_data(docs, options)
		results = self._model.predict_proba(test_data)
		results = self.get_results_dict_from_matrix(1-results)
		return results

	def displayName():
		return "Naive Bayes (sklearn)"

	def displayDescription():
		return "Multinomial naive bayes implemented in scikit-learn."
