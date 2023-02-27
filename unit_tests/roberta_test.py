from get_a_doc import get_doc, get_long
from transformers import RobertaTokenizer, RobertaModel
from torch import tensor, long
from torch.utils.data import Dataset
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np

fid = [] # input_ids
fm = [] # attention_mask

# this tests methods of using roberta on very long texts

t = RobertaTokenizer.from_pretrained("roberta-base", padding="max_length")
r = RobertaModel.from_pretrained("roberta-base")

with open(get_long(), "r", encoding="Latin-1") as f:
    ff = f.read()
    ff = t(ff)
    fid = ff["input_ids"]
    fm = ff["attention_mask"]

# one method is segmenting the texts, use roberta to classify
# each segment, then somehow aggregate the results. e.g. average.
# this may be very slow
OVERLAP = 20 # overlap between segments
s_seg_len = 512-OVERLAP # non-overlapping segment length
fid_chunks = [fid[s_seg_len*i:s_seg_len*i+512] + [1] * (s_seg_len*i+512-len(fid))
            for i in range((len(fid)//s_seg_len)+1)]
#fid_chunks[-1] += [1] * (512-len(fid_chunks[-1]))

fm_chunks = [fm[s_seg_len*i:s_seg_len*i+512] + [0] * (s_seg_len*i+512-len(fm))
             for i in range((len(fm)//s_seg_len)+1)]
#fm_chunks[-1] += [0] * (512-len(fm_chunks[-1]))

print(sum([1 for x in fm_chunks if len(x) != 512]))
print(sum([1 for x in fid_chunks if len(x) != 512]))


# results = r(tensor(fid_chunks, dtype=long), tensor(fm_chunks, dtype=long))
# print(results)

dddd = [[fid_chunks[i], fm_chunks[i]] for i in range(len(fid_chunks))]

# def c(data):
#     print("starting")
#     return r(tensor([data[0]], dtype=long), tensor([data[1]], dtype=long))

# with Pool(12) as p:
#     all_results = p.map(c, dddd)
# print(all_results)

all_results = []

print("how many 512-long segments", len(dddd))

for j in tqdm(range(len(dddd))):
    if j%400 != 0: continue
    results = r(tensor([dddd[j][0]], dtype=long), tensor([dddd[j][1]], dtype=long))
    all_results.append(results[-1][-1].detach().tolist())

all_results = np.array(all_results)

print(np.mean(all_results, axis=0))
