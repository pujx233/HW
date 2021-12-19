from bert4keras.backend import keras, set_gelu, K
from bert4keras.tokenizers import Tokenizer
from bert4keras.snippets import sequence_padding, DataGenerator
from bert4keras.snippets import open
from sklearn.metrics import precision_score, recall_score, f1_score
from configs import *


def load_data(filename):
    D = []
    with open(filename, encoding='utf-8') as f:
        for l in f:
            text1, text2, label = l.strip().split('\t')
            D.append((text1, text2, int(label)))
    return D


def evaluate(data, model, is_print=False):
    index = 1
    total, right = 0., 0.
    all_pred, all_true = [], []
    for x_true, y_true in data:
        y_pred = model.predict(x_true).argmax(axis=1)
        y_true = y_true[:, 0]
        total += len(y_true)
        right += (y_true == y_pred).sum()
        if not is_print:
            continue
        all_pred.extend(y_pred)
        all_true.extend(y_true)
        i = 0
        for y in y_pred:
            print('index:', index, '\tresult:', y, '\tgt:', y_true[i])
            index += 1
            i += 1

    if is_print:
        print('------Weighted------')
        print('Weighted precision: %.4f' % precision_score(
            all_true, all_pred, average='weighted'))
        print('Weighted recall: %.4f' % recall_score(
            all_true, all_pred, average='weighted'))
        print('Weighted f1: %.4f' % f1_score(
            all_true, all_pred, average='weighted'))

        print('------Macro------')
        print('Macro precision: %.4f' % precision_score(all_true, all_pred, average='macro'))
        print('Macro recall: %.4f' % recall_score(all_true, all_pred, average='macro'))
        print('Macro f1: %.4f' % f1_score(all_true, all_pred, average='macro'))

        print('------Micro------')
        print('Micro precision: %.4f' % precision_score(all_true, all_pred, average='micro'))
        print('Micro recall: %.4f' % recall_score(all_true, all_pred, average='micro'))
        print('Micro f1: %.4f' % f1_score(all_true, all_pred, average='micro'))
        print('\n')

    return right / total


class data_generator(DataGenerator):
    def __init__(self, data, batch_size, dict_path):
        super().__init__(data, batch_size)
        self.tokenizer = Tokenizer(dict_path, do_lower_case=True)


    def __iter__(self, random=False):
        batch_token_ids, batch_segment_ids, batch_labels = [], [], []
        for is_end, (text1, text2, label) in self.sample(random):
            token_ids, segment_ids = self.tokenizer.encode(
                text1, text2, maxlen=maxlen
            )
            batch_token_ids.append(token_ids)
            batch_segment_ids.append(segment_ids)
            batch_labels.append([label])
            if len(batch_token_ids) == self.batch_size or is_end:
                batch_token_ids = sequence_padding(batch_token_ids)
                batch_segment_ids = sequence_padding(batch_segment_ids)
                batch_labels = sequence_padding(batch_labels)
                yield [batch_token_ids, batch_segment_ids], batch_labels
                batch_token_ids, batch_segment_ids, batch_labels = [], [], []

class Evaluator(keras.callbacks.Callback):
    """评估与保存
    """

    def __init__(self, model, valid_generator, test_generator=None):
        self.best_val_acc = 0.
        self.model = model
        self.valid_generator = valid_generator
        self.test_generator = test_generator

    def on_epoch_end(self, epoch, logs=None):
        val_acc = evaluate(self.valid_generator, self.model)
        if val_acc > self.best_val_acc:
            self.best_val_acc = val_acc
            self.model.save_weights(weights_path)
        if self.test_generator is not None:
            test_acc = evaluate(self.test_generator, self.model)
            print(u'val_acc: %.5f, best_val_acc: %.5f, test_acc: %.5f\n' % (val_acc, self.best_val_acc, test_acc))
        else:
            print(u'val_acc: %.5f, best_val_acc: %.5f\n' % (val_acc, self.best_val_acc))

