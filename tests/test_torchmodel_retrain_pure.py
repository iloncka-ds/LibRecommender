import os
from pathlib import Path

import pandas as pd
import torch

from libreco.algorithms import NGCF
from libreco.data import DataInfo, DatasetPure, split_by_ratio_chrono
from libreco.evaluation import evaluate
from tests.utils_path import SAVE_PATH, remove_path
from tests.utils_pred import ptest_preds
from tests.utils_reco import ptest_recommends


def test_torchmodel_retrain_pure():
    data_path = os.path.join(
        str(Path(os.path.realpath(__file__)).parent),
        "sample_data",
        "sample_movielens_rating.dat",
    )
    all_data = pd.read_csv(
        data_path, sep="::", names=["user", "item", "label", "time"], engine="python"
    )
    # use first half data as first training part
    first_half_data = all_data[: (len(all_data) // 2)]
    train_data, eval_data = split_by_ratio_chrono(first_half_data, test_size=0.2)
    train_data, data_info = DatasetPure.build_trainset(train_data)
    eval_data = DatasetPure.build_evalset(eval_data)
    train_data.build_negative_samples(data_info, seed=2022)
    eval_data.build_negative_samples(data_info, seed=2222)

    model = NGCF(
        "ranking",
        data_info,
        embed_size=16,
        n_epochs=1,
        lr=1e-3,
        lr_decay=False,
        reg=None,
        epsilon=1e-8,
        amsgrad=False,
        batch_size=2048,
        num_neg=1,
        node_dropout=0.2,
        message_dropout=0.2,
        hidden_units="64,64,64",
        device=torch.device("cpu"),
    )
    model.fit(
        train_data,
        verbose=2,
        shuffle=True,
        eval_data=eval_data,
        metrics=[
            "loss",
            "balanced_accuracy",
            "roc_auc",
            "pr_auc",
            "precision",
            "recall",
            "map",
            "ndcg",
        ],
    )
    eval_result = evaluate(
        model,
        eval_data,
        eval_batch_size=8192,
        k=10,
        metrics=["roc_auc", "pr_auc", "precision", "recall", "map", "ndcg"],
        neg_sample=True,
        update_features=False,
        seed=2222,
    )

    data_info.save(path=SAVE_PATH, model_name="ngcf_model")
    model.save(
        path=SAVE_PATH, model_name="ngcf_model", manual=True, inference_only=False
    )

    # ========================== load and retrain =============================
    new_data_info = DataInfo.load(SAVE_PATH, model_name="ngcf_model")

    # use second half data as second training part
    second_half_data = all_data[(len(all_data) // 2) :]
    train_data_orig, eval_data_orig = split_by_ratio_chrono(
        second_half_data, test_size=0.2
    )
    train_data, new_data_info = DatasetPure.build_trainset(
        train_data_orig, revolution=True, data_info=new_data_info, merge_behavior=True
    )
    eval_data = DatasetPure.build_evalset(
        eval_data_orig, revolution=True, data_info=new_data_info
    )
    train_data.build_negative_samples(new_data_info, seed=2022)
    eval_data.build_negative_samples(new_data_info, seed=2222)

    new_model = NGCF(
        "ranking",
        new_data_info,
        embed_size=16,
        n_epochs=1,
        lr=1e-3,
        lr_decay=False,
        reg=None,
        epsilon=1e-8,
        amsgrad=True,  # change amsgrad
        batch_size=2048,
        num_neg=1,
        node_dropout=0.2,
        message_dropout=0.2,
        hidden_units="64,64,64",
        device=torch.device("cpu"),
    )
    new_model.rebuild_model(path=SAVE_PATH, model_name="ngcf_model")
    new_model.fit(
        train_data,
        verbose=2,
        shuffle=True,
        eval_data=eval_data,
        metrics=[
            "loss",
            "balanced_accuracy",
            "roc_auc",
            "pr_auc",
            "precision",
            "recall",
            "map",
            "ndcg",
        ],
    )
    ptest_preds(new_model, "ranking", second_half_data, with_feats=False)
    ptest_recommends(new_model, new_data_info, second_half_data, with_feats=False)

    new_eval_result = evaluate(
        new_model,
        eval_data_orig,
        eval_batch_size=8192,
        k=10,
        metrics=["roc_auc", "pr_auc", "precision", "recall", "map", "ndcg"],
        neg_sample=True,
        update_features=False,
        seed=2222,
    )

    assert new_eval_result["roc_auc"] != eval_result["roc_auc"]

    remove_path(SAVE_PATH)
