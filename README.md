# LibRecommender

[![Build](https://img.shields.io/github/workflow/status/massquantity/LibRecommender/Build%20wheels)](https://github.com/massquantity/LibRecommender/actions/workflows/wheels.yml)
[![CI](https://github.com/massquantity/LibRecommender/actions/workflows/ci.yml/badge.svg)](https://github.com/massquantity/LibRecommender/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/massquantity/LibRecommender/branch/master/graph/badge.svg?token=BYOYFBUJRL)](https://codecov.io/gh/massquantity/LibRecommender)
[![pypi](https://img.shields.io/pypi/v/LibRecommender?color=blue)](https://pypi.org/project/LibRecommender/)
[![Downloads](https://static.pepy.tech/personalized-badge/librecommender?period=total&units=international_system&left_color=grey&right_color=lightgrey&left_text=Downloads)](https://pepy.tech/project/librecommender)
[![python versions](https://img.shields.io/pypi/pyversions/LibRecommender?logo=python&logoColor=ffffba)](https://pypi.org/project/LibRecommender/)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/860f0cb5339c41fba9bee5770d09be47)](https://www.codacy.com/gh/massquantity/LibRecommender/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=massquantity/LibRecommender&amp;utm_campaign=Badge_Grade)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-%23ffdfba)](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-%23ffdfba)
[![License](https://img.shields.io/github/license/massquantity/LibRecommender?color=ff69b4)](https://github.com/massquantity/LibRecommender/blob/master/LICENSE)


## Overview

**LibRecommender** is an easy-to-use recommender system focused on end-to-end recommendation. The main features are:

+ Implemented a number of popular recommendation algorithms such as FM, DIN, LightGCN etc, [see full algorithm list](#references).
+ A hybrid recommender system, which allows user to use either collaborative-filtering or content-based features. New features can be added on the fly.
+ Low memory usage, automatically convert categorical and multi-value categorical features to sparse representation.
+ Support training for both explicit and implicit datasets, and negative sampling can be used for implicit dataset.
+ Provide end-to-end workflow, i.e. data handling / preprocessing -> model training -> evaluate -> serving.
+ Support cold-start prediction and recommendation.
+ Provide unified and friendly API for all algorithms. Easy to retrain model with new users/items.



## Usage

#### _pure collaborative-filtering example_ : 

```python
import numpy as np
import pandas as pd
from libreco.data import random_split, DatasetPure
from libreco.algorithms import SVDpp  # pure data, algorithm SVD++
from libreco.evaluation import evaluate

data = pd.read_csv("examples/sample_data/sample_movielens_rating.dat", sep="::",
                   names=["user", "item", "label", "time"])

# split whole data into three folds for training, evaluating and testing
train_data, eval_data, test_data = random_split(data, multi_ratios=[0.8, 0.1, 0.1])

train_data, data_info = DatasetPure.build_trainset(train_data)
eval_data = DatasetPure.build_evalset(eval_data)
test_data = DatasetPure.build_testset(test_data)
print(data_info)   # n_users: 5894, n_items: 3253, data sparsity: 0.4172 %

svdpp = SVDpp(task="rating", data_info=data_info, embed_size=16, n_epochs=3, lr=0.001,
              reg=None, batch_size=256)
# monitor metrics on eval_data during training
svdpp.fit(train_data, verbose=2, eval_data=eval_data, metrics=["rmse", "mae", "r2"])

# do final evaluation on test data
print("evaluate_result: ", evaluate(model=svdpp, data=test_data,
                                    metrics=["rmse", "mae"]))
# predict preference of user 2211 to item 110
print("prediction: ", svdpp.predict(user=2211, item=110))
# recommend 7 items for user 2211
print("recommendation: ", svdpp.recommend_user(user=2211, n_rec=7))

# cold-start prediction
print("cold prediction: ", svdpp.predict(user="ccc", item="not item",
                                         cold_start="average"))
# cold-start recommendation
print("cold recommendation: ", svdpp.recommend_user(user="are we good?",
                                                    n_rec=7,
                                                    cold_start="popular"))
```

#### _include features example_ : 

```python
import numpy as np
import pandas as pd
from libreco.data import split_by_ratio_chrono, DatasetFeat
from libreco.algorithms import YouTubeRanking  # feat data, algorithm YouTubeRanking

data = pd.read_csv("examples/sample_data/sample_movielens_merged.csv", sep=",", header=0)
data["label"] = 1  # convert to implicit data and do negative sampling afterwards

# split into train and test data based on time
train_data, test_data = split_by_ratio_chrono(data, test_size=0.2)

# specify complete columns information
sparse_col = ["sex", "occupation", "genre1", "genre2", "genre3"]
dense_col = ["age"]
user_col = ["sex", "age", "occupation"]
item_col = ["genre1", "genre2", "genre3"]

train_data, data_info = DatasetFeat.build_trainset(
    train_data, user_col, item_col, sparse_col, dense_col
)
test_data = DatasetFeat.build_testset(test_data)
train_data.build_negative_samples(data_info)  # sample negative items for each record
test_data.build_negative_samples(data_info)
print(data_info)  # n_users: 5962, n_items: 3226, data sparsity: 0.4185 %

ytb_ranking = YouTubeRanking(task="ranking", data_info=data_info, embed_size=16,
                             n_epochs=3, lr=1e-4, batch_size=512, use_bn=True,
                             hidden_units="128,64,32")
ytb_ranking.fit(train_data, verbose=2, shuffle=True, eval_data=test_data,
                metrics=["loss", "roc_auc", "precision", "recall", "map", "ndcg"])

# predict preference of user 2211 to item 110
print("prediction: ", ytb_ranking.predict(user=2211, item=110))
# recommend 7 items for user 2211
print("recommendation(id, probability): ", ytb_ranking.recommend_user(user=2211, n_rec=7))

# cold-start prediction
print("cold prediction: ", ytb_ranking.predict(user="ccc", item="not item",
                                               cold_start="average"))
# cold-start recommendation
print("cold recommendation: ", ytb_ranking.recommend_user(user="are we good?",
                                                          n_rec=7,
                                                          cold_start="popular"))
```

### For more examples and usages, see [User Guide](https://github.com/massquantity/LibRecommender/tree/master/examples#user-guide)



## Data Format

JUST normal data format, each line represents a sample. One thing is important, the model assumes that `user`, `item`, and `label` column index are 0, 1, and 2, respectively. You may wish to change the column order if that's not the case. Take for Example, the `movielens-1m` dataset:

> 1::1193::5::978300760<br>
> 1::661::3::978302109<br>
> 1::914::3::978301968<br>
> 1::3408::4::978300275

Besides, if you want to use some other meta features (e.g., age, sex, category etc.),  you need to tell the model which columns are [`sparse_col`, `dense_col`, `user_col`, `item_col`], which means all features must be in a same table. See above `YouTubeRanking` for example.

**Also note that your data should not contain missing values.**



## Serving

For how to serve a trained model in LibRecommender, see [Serving Guide](https://github.com/massquantity/LibRecommender/tree/master/libserving) .



## Installation & Dependencies 

From pypi : &nbsp;

```shell
$ pip install LibRecommender
```

To build from source, you 'll first need [Cython](<https://cython.org/>) and [Numpy](<https://numpy.org/>):

```shell
$ # pip install numpy cython
$ git clone https://github.com/massquantity/LibRecommender.git
$ cd LibRecommender
$ python setup.py install
```



#### Basic Dependencies for [`libreco`](https://github.com/massquantity/LibRecommender/tree/master/libreco):

- Python >= 3.6
- TensorFlow >= 1.15
- PyTorch >= 1.10
- Numpy >= 1.19.5
- Cython >= 0.29.0
- Pandas >= 1.0.0
- Scipy >= 1.2.1
- scikit-learn >= 0.20.0
- gensim >= 4.0.0
- tqdm
- [nmslib](https://github.com/nmslib/nmslib) (optional)

LibRecommender is tested under TensorFlow 1.15, 2.5, 2.8 and 2.10. If you encounter any problem during running, feel free to open an issue.

**Known issue**: Sometimes one may encounter errors like `ValueError: numpy.ndarray size changed, may indicate binary incompatibility. Expected 88 from C header, got 80 from PyObject`. In this case try upgrading numpy, and version 1.22.0 or higher is probably a safe option.

The table below shows some compatible version combinations: 

| Python |     Numpy      |      TensorFlow      |          OS           |
| :----: | :------------: | :------------------: | :-------------------: |
|  3.6   |     1.19.5     |      1.15, 2.5       | linux, windows, macos |
|  3.7   | 1.20.3, 1.21.6 | 1.15, 2.5, 2.8, 2.10 | linux, windows, macos |
|  3.8   | 1.22.4, 1.23.2 |    2.5, 2.8, 2.10    | linux, windows, macos |
|  3.9   | 1.22.4, 1.23.2 |    2.5, 2.8, 2.10    | linux, windows, macos |
|  3.10  | 1.22.4, 1.23.2 |      2.8, 2.10       | linux, windows, macos |


#### Optional Dependencies for [`libserving`](https://github.com/massquantity/LibRecommender/tree/master/libserving):

+ Python >= 3.7 (Many of the below libraries require at least 3.7)
+ sanic >= 22.3
+ requests
+ aiohttp
+ pydantic
+ [ujson](https://github.com/ultrajson/ultrajson)
+ [redis](<https://redis.io/>)
+ [redis-py](https://github.com/andymccurdy/redis-py) >= 4.2.0
+ [faiss](https://github.com/facebookresearch/faiss) >= 1.5.2
+ [TensorFlow Serving](<https://github.com/tensorflow/serving>) == 2.8.2

## Docker
One can also use the library in a docker container without installing dependencies, see [Docker](https://github.com/massquantity/LibRecommender/tree/master/docker).

## References

|     Algorithm     | Category<sup><a href="#fn1" id="ref1">1</a></sup> | Backend | Sequence<sup><a href="#fn2" id="ref2">2</a></sup> | Graph<sup><a href="#fn3" id="ref3">3</a></sup> | Embedding<sup><a href="#fn4" id="ref4">4</a></sup> | Paper                                                        |
|:-----------------:| :------: | :----------------------------------------------------------: |:---------------------------------:|:---------------------------------:|:---------------------------------:|-----------------------------------|
|  userCF / itemCF  |   pure   |   Cython   |      |      |      | [Item-Based Collaborative Filtering Recommendation Algorithms](http://www.ra.ethz.ch/cdstore/www10/papers/pdf/p519.pdf) |
|        SVD        |   pure   |   TensorFlow1   |      |      |   :heavy_check_mark:   | [Matrix Factorization Techniques for Recommender Systems](https://datajobs.com/data-science-repo/Recommender-Systems-[Netflix].pdf) |
|       SVD++       |   pure   |   TensorFlow1   |      |      |   :heavy_check_mark:   | [Factorization Meets the Neighborhood: a Multifaceted Collaborative Filtering Model](https://dl.acm.org/citation.cfm?id=1401944) |
|        ALS        |   pure   |   Cython   |      |      |   :heavy_check_mark:   | 1. [Matrix Completion via Alternating Least Square(ALS)](https://stanford.edu/~rezab/classes/cme323/S15/notes/lec14.pdf)  <br>2. [Collaborative Filtering for Implicit Feedback Datasets](http://yifanhu.net/PUB/cf.pdf)  <br>3. [Applications of the Conjugate Gradient Method for Implicit Feedback Collaborative Filtering](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.379.6473&rep=rep1&type=pdf) |
|        NCF        |   pure   |   TensorFlow1   |      |      |      | [Neural Collaborative Filtering](https://arxiv.org/pdf/1708.05031.pdf) |
|        BPR        |   pure   |   Cython, TensorFlow1   |      |      |   :heavy_check_mark:   | [BPR: Bayesian Personalized Ranking from Implicit Feedback](https://arxiv.org/ftp/arxiv/papers/1205/1205.2618.pdf) |
|    Wide & Deep    |   feat   |   TensorFlow1   |      |      |      | [Wide & Deep Learning for Recommender Systems](https://arxiv.org/pdf/1606.07792.pdf) |
|        FM         |   feat   |   TensorFlow1   |      |      |      | [Factorization Machines](https://www.csie.ntu.edu.tw/~b97053/paper/Rendle2010FM.pdf) |
|      DeepFM       |   feat   |   TensorFlow1   |      |      |      | [DeepFM: A Factorization-Machine based Neural Network for CTR Prediction](https://arxiv.org/pdf/1703.04247.pdf) |
| YouTubeRetrieval  |   feat   |   TensorFlow1   |   :heavy_check_mark:   |      |   :heavy_check_mark:   | [Deep Neural Networks for YouTube Recommendations](<https://static.googleusercontent.com/media/research.google.com/zh-CN//pubs/archive/45530.pdf>) |
|  YouTubeRanking   | feat | TensorFlow1 | :heavy_check_mark: |  |  | [Deep Neural Networks for YouTube Recommendations](<https://static.googleusercontent.com/media/research.google.com/zh-CN//pubs/archive/45530.pdf>) |
|      AutoInt      | feat | TensorFlow1 |  |  |  | [AutoInt: Automatic Feature Interaction Learning via Self-Attentive Neural Networks](https://arxiv.org/pdf/1810.11921.pdf) |
|        DIN        |   feat   |   TensorFlow1   |   :heavy_check_mark:   |      |      | [Deep Interest Network for Click-Through Rate Prediction](https://arxiv.org/pdf/1706.06978.pdf) |
|     Item2Vec      | pure | / | :heavy_check_mark: |  | :heavy_check_mark: | [Item2Vec: Neural Item Embedding for Collaborative Filtering](https://arxiv.org/pdf/1603.04259.pdf) |
| RNN4Rec / GRU4Rec | pure | TensorFlow1 | :heavy_check_mark: |  | :heavy_check_mark: | [Session-based Recommendations with Recurrent Neural Networks](https://arxiv.org/pdf/1511.06939.pdf) |
|       Caser       | pure | TensorFlow1 | :heavy_check_mark: |  | :heavy_check_mark: | [Personalized Top-N Sequential Recommendation via Convolutional Sequence Embedding](https://arxiv.org/pdf/1809.07426.pdf) |
|      WaveNet      | pure | TensorFlow1 | :heavy_check_mark: |  | :heavy_check_mark: | [WaveNet: A Generative Model for Raw Audio](https://arxiv.org/pdf/1609.03499.pdf) |
|     DeepWalk      | pure | / |  | :heavy_check_mark: | :heavy_check_mark: | [DeepWalk: Online Learning of Social Representations](https://arxiv.org/pdf/1403.6652.pdf) |
|       NGCF        | pure | PyTorch |  | :heavy_check_mark: | :heavy_check_mark: | [Neural Graph Collaborative Filtering](https://arxiv.org/pdf/1905.08108.pdf) |
|     LightGCN      | pure | PyTorch |  | :heavy_check_mark: | :heavy_check_mark: | [LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation](https://arxiv.org/pdf/2002.02126.pdf) |

> <sup id="fn1">[1] **Category**: `pure` means collaborative-filtering algorithms which only use behavior data,  `feat` means other side-features can be included. <a href="#ref1" title="Jump back to footnote 1 in the text.">↩</a></sup>
> 
> <sup id="fn2">[2] **Sequence**: Algorithms that leverage user behavior sequence. <a href="#ref2" title="Jump back to footnote 2 in the text.">↩</a></sup>
> 
> <sup id="fn3">[3] **Graph**: Algorithms that leverage graph information, including Graph Embedding (GE) and Graph Neural Network (GNN) . <a href="#ref3" title="Jump back to footnote 3 in the text.">↩</a></sup>
> 
> <sup id="fn4">[4] **Embedding**: Algorithms that can generate final user and item embeddings. <a href="#ref4" title="Jump back to footnote 4 in the text.">↩</a></sup>



## License

#### MIT

<br>

