from generics.Embedding import Embedding
from backend.Histograms import generateAbsoluteHistogram as gh
from backend import PrepareNumbers as pn
import numpy as np
from transformers import RobertaModel, RobertaTokenizer
from multiprocessing import Pool, cpu_count
from torch.cuda import is_available as cuda_is_available
from torch import tensor, long as long_int
from gc import collect as collect_garbage
from multiprocessing import Pipe
from tqdm import tqdm

class Roberta(Embedding):

	convert_from = "canonicized text"
	model_variant = "roberta-base"
	device = "Try GPU"
	lowercase = "True"
	long_text_method = "head only"
	long_text_overlap = 0
	_MLEN = 512 # length of longest segment that roberta accepts
	_MSKI = 1 # roberta input index for a padded token. Should be 1.

	_variable_options = {
		"convert_from": {"options": ["canonicized text", "features (SLOW)"], "type": "OptionMenu", "default": 0,
			"displayed_name": "Convert from"},
		"model_variant": {"options": ["roberta-base", "roberta-large"], "type": "OptionMenu", "default": 0,
			"displayed_name": "Model Variant"},
		# "device": {"options": ["Try GPU", "CPU"], "type": "OptionMenu", "default": 0,
		# 	"displayed_name": "Compute Device"},
		"lowercase": {"options": ["True", "False"], "default": 0, "displayed_name": "Use Lowercase"},
		"long_text_method": {"options": [
				"head only", "tail only", "average all (SLOW)",
				"average every 4",
				"average every 16", "average every 64", "average every 128",
			], "default": 0,
			"displayed_name": "Long text analysis"},
		# "average_every": {"options": range(0, 257), "resolution": 1, "type": "Slider", "default": 0,
		# 	"displayed_name": "Average every:"},
		"long_text_overlap": {"options": range(0, 257), "type": "Slider", "default": 0, "displayed_name": "Long text:\nsegment overlap"}
	}

	def after_init(self, **options):
		self._tokenizer_args = {"padding": "max_length"}
		self._tokenizer = None
		self._model = None

	def set_attr(self, var, value):
		"""Custom way to set attributes"""
		self.__dict__[var] = value
		# if var == "long_text_method":
		# 	if value == "average some...":
		# 		self._variable_options["average_skip"]["show"] = True
		# 		self._variable_options["long_text_overlap"]["show"] = True
		# 	else:
		# 		self._variable_options["average_skip"]["show"] = False
		# 		self._variable_options["long_text_overlap"]["show"] = False
		# 	return True
		return

	def tokenizer_pool(self, content):
		"""Wrapper for a process in the pool, defined so the function passed to pool only takes one argument.
		Other arbitrary arguments are set in self._tokenizer_args and passed here."""
		doc_tokenized = self._tokenizer(content, **self._tokenizer_args)
		return doc_tokenized

	def convert(self, docs, pipe: Pipe=None):
		"""Convert and assign to Documents.numbers"""
		# docs: list of documents
		# padding = True
		if pipe is not None: pipe.send("RoBERTa: tokenizing"); pipe.send(True)
		self._tokenizer = RobertaTokenizer.from_pretrained(
			self.model_variant, truncation=True, do_lower_case=(self.lowercase=="True"),
			padding=True, padding_side="right",
		)
		if self.convert_from == "canonicized text":
			print("tokenizing from text")
			text = [d.text for d in docs]
			with Pool(cpu_count()-1) as p:
				tokenized = p.map(self.tokenizer_pool, [d.text for d in docs]) #kwargs, padding="max_length"
			# tokenized: [{"input_ids": ..., "attention_mask": ...}, {...}, ...]
			del p
			ids = [d["input_ids"] for d in tokenized]
			mask = [d["attention_mask"] for d in tokenized]
			del self._tokenizer; collect_garbage()

		elif self.convert_from.startswith("features"):
			print("tokenizing from features")
			# [{input_ids, mask}, {input_id, mask}, ...]
			self._tokenizer_args["padding"] = "do_not_pad"
			with Pool(cpu_count()-1) as p:
				events = p.map(self.tokenizer_pool, [d.eventSet for d in docs])
			bos_id = events[0]["input_ids"][0][0]; eos_id = events[-1]["input_ids"][-1][-1]
			bos_mask = events[0]["attention_mask"][0][0]; eos_mask = events[-1]["attention_mask"][-1][-1]
			del self._tokenizer; collect_garbage()

			ids = []; mask = []
			for d in events:
				# d: document
				ids.append([bos_id]); mask.append([bos_mask])
				# d: {input_ids: ..., mask: ...}
				for i in range(len(d["input_ids"])):
					ids[-1] += d["input_ids"][i][1:-1]
					mask[-1] += d["attention_mask"][i][1:-1]
				ids[-1].append(eos_id); mask[-1].append(eos_mask)
			segmenting = False
		else: raise ValueError("Unknown option for Roberta.convert_from")

		# here, 'ids' and 'mask' are the two variables to pass to roberta
		if pipe is not None: pipe.send("RoBERTa: embedding")
		roberta = RobertaModel.from_pretrained(self.model_variant)
		#device = "cuda" if (self.device.lower() == "try gpu" and cuda_is_available()) else "cpu"

		numbers = []
		if self.long_text_method.startswith("average every") or self.long_text_method.startswith("average all"):
			try: avg_skip = int(self.long_text_method.split()[-1])
			except ValueError: avg_skip = 1

			n_docs = len(ids)
			for doc_index in range(n_docs):
				if pipe is not None:
					progress_begin = doc_index * 100 / n_docs
					progress_end = (doc_index + 1) * 100 / n_docs
					pipe.send(progress_begin)
				# this is the length of each non-overlapping segment
				doc_input_ids = ids[doc_index]
				doc_attn_mask = mask[doc_index]
				seg_len = 512 - self.long_text_overlap
				# construct 512-long chunks, pad to 512 if needed.
				# this is for when the doc is longer than 512 tokens long.
				doc_input_ids_chunks = [
					doc_input_ids[seg_len*i:seg_len*i+self._MLEN] +\
					[self._MSKI] * (seg_len*i+self._MLEN-len(doc_input_ids))
					for i in range((len(doc_input_ids)//seg_len)+1)
				]
				doc_attn_mask_chunks = [
					doc_attn_mask[seg_len*i:seg_len*i+self._MLEN] +\
					[0] * (seg_len*i+self._MLEN-len(doc_attn_mask))
					for i in range((len(doc_attn_mask)//seg_len)+1)
				]
				n_chunks = len(doc_input_ids_chunks)

				document_result = [] # embedding for all chunks in a doc
				print("Embedding", docs[doc_index].title)
				for chunk_index in tqdm(range(0, n_chunks, avg_skip)):
					# embed each chunk
					if chunk_index % avg_skip != 0: continue
					if pipe is not None:
						pipe.send((chunk_index/n_chunks)*progress_end+(1-chunk_index/n_chunks)*progress_begin)
					results = roberta(
						tensor([doc_input_ids_chunks[chunk_index]], dtype=long_int),
						tensor([doc_attn_mask_chunks[chunk_index]], dtype=long_int)
					)
					document_result.append(results[-1][-1].detach().tolist())
				document_result = np.mean(document_result, axis=0).tolist()
				docs[doc_index].numbers = document_result
				numbers.append(document_result)
			numbers = np.array(numbers)

		elif self.long_text_method == "head only" or self.long_text_method == "tail only":
			n_docs = len(ids)
			numbers = []
			for doc_index in range(n_docs):
				if pipe is not None: pipe.send(doc_index * 100 / n_docs)
				# for input_ids and attention_mask:
				# pad to 512 if too short, truncate to 512 if too long.
				doc_ids = (ids[doc_index] + [self._MSKI] * (self._MLEN - len(ids[doc_index])))
				doc_mask = (mask[doc_index] + [0] * (self._MLEN - len(ids[doc_index])))
				if self.long_text_method == "head only":
					doc_ids = doc_ids[:512]; doc_mask = doc_mask[:512]
				elif self.long_text_method == "tail only":
					doc_ids = doc_ids[-512:]; doc_mask = doc_mask[-512:]
				results = roberta(
					tensor([doc_ids], dtype=long_int),
					tensor([doc_mask], dtype=long_int)
				)
				doc_result = results[-1][-1].detach().tolist()
				docs[doc_index].numbers = doc_result
				numbers.append(doc_result)
			numbers = np.array(numbers)
		del roberta; collect_garbage()
		return numbers

	def displayDescription():
		return ("RoBERTa language model. The model will be cached if using for the first time. Each variant is ~1GB.\n\n"+\
			"Compute Device: if GPU, PyGAAP will try to push data/model to GPU, if unsuccessful, fallback to CPU.\n"+\
			"Convert from text: convert from canonicized text, ignoring all event drivers and event culling\n"+\
			"Convert from features: use events from event drivers and event culling.\n\n"+\
			"\t**Can be slow for long docs if the output from features is long\n"+\
			"Long text method: what to do with texts with more than 512 tokens (max sequence length for RoBERTa)\n"+\
			"\tAverage every <n>: Embed every <n> sequence for every doc and average the results\n"+\
			"\tAverage all: Embed every chunk of 512-length sequence. **Will be very slow for long docs.\n"+\
			"\tHead/tail only: embed only the first/last 512 tokens.")

	def displayName():
		return "RoBERTa"