# 数据预处理

## 提取所需列

- 观察数据可知对语义影响最大且较好判断的三项为A2、A4和A5，只关注着三列

## 降噪

- 很多数据有无关语义的词，例如日期，地名，介词之类，可以通过剔除这些数据来实现降噪

### 去除单位的地名前缀，且分词，提炼出重点

- 例如将南京市交通运输局提炼为【交通 运输】

### 每一列取频率高的几个token，默认不多于3个

- 有些数据项的词组过多，可以保留出高频的几项

## 计算语义相似度

- BM25：[https://www.cnblogs.com/shona/p/11971310.html)]，以A5为键，每个A5项对应的A4或者A2词组视作一篇文章，进行后续计算.

- BERT：[https://github.com/bojone/BERT-whitening/tree/main/chn]，通过bert得到每一项的句子向量，再计算两项向量的距离（例如A4和A5一对比较），得到相似度，低于一定阈值视为异常。使用RoFormer预训练模型.

# 注意事项
- 运行环境：python--3.9.7, tensorflow-keras--2.6, bert4keras
- 先执行pre_process.py得到预处理后的数据，再执行eval.py计算语义相似度
- 执行pre_process.py时可根据需要通过改变FLAG中项的布尔值来选择运行哪些操作，但需遵从给定顺序
- 需要先下载模型，由于预训练模型过大，故单独放出链接：[https://open.zhuiyi.ai/releases/nlp/models/zhuiyi/chinese_roformer_L-12_H-768_A-12.zip]