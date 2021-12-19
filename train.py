from utils import *
from configs import *
from model import model

# 加载数据集
train_generator = data_generator(load_data(train_path), batch_size, dict_path)
valid_generator = data_generator(load_data(valid_path), batch_size, dict_path)

model.fit(
    train_generator.forfit(),
    steps_per_epoch=len(train_generator),
    epochs=20,
    callbacks=[Evaluator(model, valid_generator)]
)
