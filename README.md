#### 运行环境：python3.7，具体看requirements.txt，在Google Colab上进行训练

# 运行步骤

- 先运行pre_process.py来做数据预处理（本数据集已附带经过预处理的结果文件，可以不跑此程序）

- bert模型下载（密码4cMG）：http://pan.iflytek.com/#/link/653637473FFF242C3869D77026C9BDB5

- 还需下载针对目标域的预训练权重（或者使用train.py自行训练得到权重）：https://drive.google.com/drive/folders/1-3p02yR4XNB1cGhZk1_H_1cwqojvEIYM?usp=sharing

- 最后使用eval.py验证，得到结果：
```
------Weighted------
Weighted precision: 0.9223
Weighted recall: 0.9028
Weighted f1: 0.9102
------Macro------
Macro precision: 0.7339
Macro recall: 0.8187
Macro f1: 0.7666
------Micro------
Micro precision: 0.9028
Micro recall: 0.9028
Micro f1: 0.9028
```
- 运行截图：

  <img src="/Users/zack/Seafile/DSExp/final/assests/result.png" alt="result" />
