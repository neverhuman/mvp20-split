"""Small fixed-config GPU model and fair blending helpers."""
from __future__ import annotations

import numpy as np


def rmsle(y_true: np.ndarray, prediction: np.ndarray) -> float:
    y = np.asarray(y_true, dtype=float); p = np.clip(np.asarray(prediction, dtype=float), 0, None)
    if np.any(y < 0) or not np.all(np.isfinite(p)): raise ValueError("RMSLE requires non-negative labels and finite predictions")
    return float(np.sqrt(np.mean((np.log1p(p)-np.log1p(y))**2)))


def simplex_weights(oof: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Nonnegative least-squares weights, normalized to a simplex."""
    from scipy.optimize import nnls
    z=np.log1p(np.clip(np.asarray(oof,float), 0, None)); target=np.log1p(np.asarray(y,float)); weights,_=nnls(z,target)
    if not np.isfinite(weights).all() or weights.sum() <= 0: weights=np.ones(z.shape[1])
    return weights/weights.sum()


def fit_catboost_gpu(x_train, y_train, x_valid, y_valid, *, seed: int = 42, iterations: int = 800):
    from catboost import CatBoostRegressor
    model=CatBoostRegressor(iterations=iterations, depth=8, learning_rate=.04, loss_function="RMSE", random_seed=seed, task_type="GPU", devices="0", allow_writing_files=False, verbose=False, od_type="Iter", od_wait=60)
    model.fit(x_train, np.log1p(y_train), eval_set=(x_valid,np.log1p(y_valid)), verbose=False)
    return model, np.expm1(model.predict(x_valid))


def fit_xgboost_gpu(x_train, y_train, x_valid, y_valid, *, seed: int = 42, estimators: int = 800):
    from xgboost import XGBRegressor
    model=XGBRegressor(n_estimators=estimators,max_depth=8,learning_rate=.04,subsample=.8,colsample_bytree=.8,objective="reg:squarederror",tree_method="hist",device="cuda",random_state=seed)
    model.fit(x_train,np.log1p(y_train),eval_set=[(x_valid,np.log1p(y_valid))],verbose=False)
    return model,np.expm1(model.predict(x_valid))


def fit_lightgbm_gpu(x_train, y_train, x_valid, y_valid, *, seed: int = 42, estimators: int = 800):
    from lightgbm import LGBMRegressor
    model=LGBMRegressor(n_estimators=estimators,num_leaves=63,learning_rate=.04,subsample=.8,colsample_bytree=.8,device_type="gpu",verbosity=-1,random_state=seed)
    model.fit(x_train,np.log1p(y_train),eval_set=[(x_valid,np.log1p(y_valid))],callbacks=[])
    return model,np.expm1(model.predict(x_valid))
