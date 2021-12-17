from utils import *
import sys
import jieba
import math
from pre_process import *

jieba.initialize()

# 基本参数
model_name = 'chinese_roformer_L-12_H-768_A-12'
pooling = 'first-last-avg'
task_name = 'new-A2'
maxlen = 64
n_components = 0
simple_run = True
bm25 = True

# 加载数据集
data_path = 'dataset/pre'

dataset = {
    '%s-A25' % (task_name):
    load_data_csv('%s/%s.csv' % (data_path, task_name), ['A2', 'A5', 'A4']),
    '%s-A45' % (task_name):
    load_data_csv('%s/%s.csv' % (data_path, task_name), ['A4', 'A5'])
}

sim_set = {}
def simple_run_func(task):
    left_overs = []
    ss = {}
    index = 0
    for pair in dataset['%s-%s' % (task_name, task)]:
        a = pair[0].split(' ')
        keys = pair[1].split(' ')
        ss[index] = -1
        for key in keys:
            if key in a:
                ss[index] = 1.0
                break
        if ss[index] != 1.0:
            left_overs.append(pair)
        index += 1
    sim_set['%s-%s' % (task_name, task)] = ss
    dataset['%s-%s' % (task_name, task)] = left_overs

if simple_run:
    simple_run_func('A25')
    simple_run_func('A45')

class BM25(object):
    def __init__(self, doc):
        self.avgdl = len(doc) + 0.0
        self.doc = doc
        self.f = {}  # 每个词的出现次数
        self.idf = {}  # 存储每个词的idf值
        self.k1 = 1.5
        self.b = 0.75
        self.init()

    def init(self):
        tmp = {}
        for word in self.doc:
            tmp[word] = tmp.get(word, 0) + 1  # 存储每个文档中每个词的出现次数
        self.f = tmp
        for k in self.doc:
            self.idf[k] = math.log(0.5) - math.log(1 + 0.5)

    def sim(self, doc):
        score = 0
        d = len(self.doc)
        for word in doc:
            if word not in self.f:
                continue
            score += (self.idf[word] * self.f[word] * (self.k1 + 1) / (self.f[word] + self.k1 * (1 - self.b + self.b * d / self.avgdl)))
        return score


def bm25_func(head, name, items):
    dic = {}
    total_words = 0
    for item in items:
        dic[item[1]] = dic.get(item[1], [])
        dic[item[1]].extend(item[0].split(' '))

    bm = {}
    for key, value in dic.items():
        bm[key] = BM25(value)
    
    index = 0
    scores = sim_set[name]
    left_overs = []
    for item in items:
        while scores[index] == 1:
            index += 1
        score = bm[item[1]].sim(item[0].split(' '))
        if score < -3:
            scores[index] = 1.0
        else:
            left_overs.append(item)
        index += 1
    sim_set[name] = scores
    dataset[name] = left_overs

if bm25:
    for name, data in dataset.items():
        bm25_func(name.replace('5', ''), name, data)

# bert配置
config_path = 'dataset/model/%s/bert_config.json' % model_name
checkpoint_path = 'dataset/model/%s/bert_model.ckpt' % model_name
dict_path = 'dataset/model/%s/vocab.txt' % model_name

# 建立分词器
tokenizer = get_tokenizer(
    dict_path, pre_tokenize=lambda s: jieba.lcut(s, HMM=False)
)

# 建立模型
encoder = get_encoder(
    config_path, checkpoint_path, model='roformer', pooling=pooling
)

# 语料向量化
all_names, all_vecs = [], []
for name, data in dataset.items():
    a_vecs, b_vecs = convert_to_vecs(data, tokenizer, encoder, maxlen)
    all_names.append(name)
    all_vecs.append((a_vecs, b_vecs))

idx = 0
probs = []
# 变换，标准化，相似度
for (a_vecs, b_vecs) in all_vecs:
    a_vecs = transform_and_normalize(a_vecs)
    b_vecs = transform_and_normalize(b_vecs)
    sims = (a_vecs * b_vecs).sum(axis=1)
    index = 0
    for i in range(len(sim_set[all_names[idx]])):
        if sim_set[all_names[idx]][i] == 1.0:
            continue
        sim_set[all_names[idx]][i] = sims[index]
        index += 1
    prob = []
    for i in range(len(sim_set[all_names[idx]])):
        if sim_set[all_names[idx]][i] < 0.6:
            prob.append(i)
    idx += 1
    probs.append(prob)

ids = get_ids()

print('=======')

eval_results = []
for p in probs[0]:
    eval_result = {}
    eval_result['id'] = ids[p]
    eval_result['anomaly'] = 'A2 or A4'
    eval_results.append(eval_result)
for p in probs[1]:
    eval_result = {}
    eval_result['id'] = ids[p]
    eval_result['anomaly'] = 'A4 or A5'
    eval_results.append(eval_result)

for item in eval_results:
    print('id: %s \t anomaly: %s' % (item['id'], item['anomaly']))

with open('dataset/result.csv', 'w', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'anomaly'])
    writer.writeheader()
    for item in eval_results:
        print('id: %s \t anomaly: %s' % (item['id'], item['anomaly']))
        writer.writerow(item)
