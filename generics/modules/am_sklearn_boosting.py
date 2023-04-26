from generics.module import AnalysisMethod
from sklearn import ensemble

class sklearn_gradient_boosting(AnalysisMethod):

	loss = "log_loss"
	learning_rate = 0.1
	n_estimators = 100
	subsample_fraction = 1.0
	tolerance = 1e-4
	validation_fraction = 0.1
	log_prob = 1

	_NoDistanceFunction_ = True
	_sort_key = "boosting gradient"

	_variable_options = {
		"loss": {"options": ["log_loss", "deviance", "exponential"], "default": 0, "displayed_name": "Loss function"},
		"tolerance": {"options": [0.00001, 0.00002, 0.00005, 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05],
			"type": "OptionMenu", "default": 3, "displayed_name": "Stopping Tolerance",
			"validator": (lambda x: (x > 0.000001 and x < 0.1))},
		"learning_rate": {"options": [0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2], "default": 3,
			"displayed_name": "Learning Rate", "validator": (lambda x: (x > 0.00001 and x <= 1))},
		"n_estimators": {"options": [1, 5, 10, 20, 50, 75, 100, 200, 500, 750, 1000], "default": 6, "displayed_name": "Estimators count"},
		"subsample_fraction": {"options": [0.01, 1.0], "type": "Slider", "resolution": 0.01, "default": 1,
			"displayed_name": "Learner subsample fraction"},
		"validation_fraction": {"options": [0.05, 0.45], "type": "Slider", "resolution": 0.05, "default": 1, "displayed_name": "Fraction used for validation",
			"validator": (lambda x: (x > 0.01 and x < 0.5))},
		"log_prob": {"options": [0, 1], "type": "Tick", "default": 1, "displayed_name": "Use Log Probability"}
	}

	def train(self, train, train_data):
		train_data, train_labels = self.get_train_data_and_labels(train, train_data)
		train_labels = train_labels.flatten()
		self._model = ensemble.GradientBoostingClassifier(
			learning_rate=self.learning_rate,
			tol=self.tolerance,
			validation_fraction=self.validation_fraction,
			subsample=self.subsample_fraction,
			n_estimators=self.n_estimators,
			loss=self.loss,
		)

		self._model.fit(train_data, train_labels)
		return

	def process(self, docs, pipe=None, **options):
		self.train([d for d in docs if d.author != ""], options.get("known_numbers"))
		test_data = self.get_test_data(docs, options)
		results = self._model.predict_log_proba(test_data) \
			if self.log_prob else _model.predict_proba(test_data)
		if len(results.shape) == 1:
			results = np.array((results, 1-results)).transpose()
		results = self.get_results_dict_from_matrix(1-results)
		return results

	def displayDescription():
		return "Gradient Boosting with sklearn.emsemble.GradientBoostingClassifier"

	def displayName():
		return "Gradient boosting (sklearn)"



class sklearn_adaboost(AnalysisMethod):

	learning_rate = 0.1
	n_estimators = 100
	log_prob = 1

	_NoDistanceFunction_ = True
	_sort_key = "boosting adaptive"

	_variable_options = {
		"learning_rate": {"options": [0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2], "default": 3,
			"displayed_name": "Learning Rate", "validator": (lambda x: (x > 0.00001 and x <= 1))},
		"n_estimators": {"options": [1, 5, 10, 20, 50, 75, 100, 200, 500, 750, 1000], "default": 6, "displayed_name": "Estimators count"},
		"log_prob": {"options": [0, 1], "type": "Tick", "default": 1, "displayed_name": "Use Log Probability"}
	}

	def train(self, train, train_data):
		train_data, train_labels = self.get_train_data_and_labels(train, train_data)
		train_labels = train_labels.flatten()
		self._model = ensemble.GradientBoostingClassifier(
			learning_rate=self.learning_rate,
			n_estimators=self.n_estimators,
		)
		self._model.fit(train_data, train_labels)
		return

	def process(self, docs, pipe=None, **options):
		self.train([d for d in docs if d.author != ""], options.get("known_numbers"))
		test_data = self.get_test_data(docs, options)
		results = self._model.predict_log_proba(test_data) \
			if self.log_prob else _model.predict_proba(test_data)
		if len(results.shape) == 1:
			results = np.array((results, 1-results)).transpose()
		results = self.get_results_dict_from_matrix(1-results)
		return results

	def displayDescription():
		return "Sklearn's adaptive boosting (Adaboost) with decision trees"

	def displayName():
		return "Adaptive boosting (sklearn)"