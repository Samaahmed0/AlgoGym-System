
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from recommender.features import FEATURE_COLUMNS


class RankerModel:
    def __init__(self, model, feature_columns: list[str] | None = None) -> None:
        self.model = model
        self.feature_columns = feature_columns or list(FEATURE_COLUMNS)

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
        cols = list(FEATURE_COLUMNS)
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
) -> tuple[RankerModel, dict]:
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split

    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[feature_cols]
    y = df["label"].astype(float)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=val_frac, random_state=seed
    )

    params = {
        "objective": "regression",
        "metric": "rmse",
        "verbosity": -1,
        "seed": seed,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "device": device,
    }
    train_set = lgb.Dataset(X_train, label=y_train)
    val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
    booster = lgb.train(
        params,
        train_set,
        num_boost_round=200,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(20, verbose=False)],
    )

    model = RankerModel(booster, feature_cols)
    preds = model.predict(X_val)
    rmse = float(np.sqrt(np.mean((preds - y_val.values) ** 2)))
    metrics = {"val_rmse": rmse, "n_train": len(X_train), "n_val": len(X_val)}
    return model, metrics
