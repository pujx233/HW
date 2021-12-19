import os

os.environ['TF_KERAS'] = '1'

maxlen = 128
batch_size = 64
config_path = 'models/chinese_wwm_ext_L-12_H-768_A-12/bert_config.json'
checkpoint_path = 'models/chinese_wwm_ext_L-12_H-768_A-12/bert_model.ckpt'
dict_path = 'models/chinese_wwm_ext_L-12_H-768_A-12/vocab.txt'
weights_path = 'models/best_model.weights'
train_path = 'dataset/zw.train.data'
valid_path = 'dataset/zw.valid.data'
test_path = 'dataset/zw.test.data'
