
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from recommender.features2 import FEATURE_COLUMNS_V2

__all__ = ["RankerModel", "train_ranker", "FEATURE_COLUMNS_V2"]


class RankerModel:
    def __init__(self, model, feature_columns: list[str] | None = None) -> None:
        self.model = model
        self.feature_columns = feature_columns or list(FEATURE_COLUMNS_V2)

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            X = X[self.feature_columns].values
        return self.model.predict(X)

    def save(self, model_path: Path, schema_path: Path) -> None:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, model_path)
        schema_path.write_text(
            json.dumps({"feature_columns": self.feature_columns}, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, model_path: Path, schema_path: Path | None = None) -> RankerModel:
        model = joblib.load(model_path)
        cols = list(FEATURE_COLUMNS_V2)
        if schema_path is not None and schema_path.exists():
            data = json.loads(schema_path.read_text(encoding="utf-8"))
            cols = data.get("feature_columns", cols)
        return cls(model, cols)


def train_ranker(
    df: pd.DataFrame,
    *,
    val_frac: float = 0.2,
    seed: int = 42,
    device: str = "cpu",
    split_by_student: bool = True,
) -> tuple[RankerModel, dict]:
    """Train LightGBM on FEATURE_COLUMNS_V2 with tuned hyperparameters."""
    import lightgbm as lgb
    from sklearn.model_selection import GroupShuffleSplit, train_test_split

    feature_cols = [c for c in FEATURE_COLUMNS_V2 if c in df.columns]
    missing = set(FEATURE_COLUMNS_V2) - set(feature_cols)
    if missing:
        raise ValueError(f"Training dataframe missing v2 feature columns: {sorted(missing)}")

    X = df[feature_cols]
    y = df["label"].astype(float)

    if split_by_student and "student_id" in df.columns:
        groups = df["student_id"]
        splitter = GroupShuffleSplit(n_splits=1, test_size=val_frac, random_state=seed)
        train_idx, val_idx = next(splitter.split(X, y, groups))
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        split_mode = "group_by_student"
    else:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=val_frac, random_state=seed
        )
        split_mode = "random_rows"

    params = {
        "objective": "regression",
        "metric": "rmse",
        "verbosity": -1,
        "seed": seed,
        "learning_rate": 0.03,
        "num_leaves": 63,
        "min_data_in_leaf": 50,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "lambda_l1": 0.1,
        "lambda_l2": 0.1,
        "device": device,
    }
    train_set = lgb.Dataset(X_train, label=y_train)
    val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
    booster = lgb.train(
        params,
        train_set,
        num_boost_round=500,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    model = RankerModel(booster, feature_cols)
    preds = model.predict(X_val)
    rmse = float(np.sqrt(np.mean((preds - y_val.values) ** 2)))
    metrics = {
        "val_rmse": rmse,
        "n_train": len(X_train),
        "n_val": len(X_val),
        "split_mode": split_mode,
        "feature_version": "v2",
        "n_features": len(feature_cols),
    }
    return model, metrics
