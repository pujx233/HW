from model import model
from utils import *
from configs import *

test_generator = data_generator(load_data(test_path), batch_size, dict_path)

model.load_weights(weights_path)
print(u'final test acc: %05f\n' % (evaluate(test_generator, model, True)))
