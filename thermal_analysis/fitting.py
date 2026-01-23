import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Tuple, List, Optional

@dataclass
class FitResult:
    slope: float
    intercept: float
    r2: float
    is_valid: bool

def extract_subset(x: np.ndarray, y: np.ndarray, indices: List[int]) -> Tuple[np.ndarray, np.ndarray]:
    """インデックスに基づいて部分配列を抽出"""
    if len(indices) == 0:
        return np.array([]), np.array([])
    return x[indices], y[indices]

def linear_regression_subset(x: np.ndarray, y: np.ndarray, indices: Optional[List[int]] = None) -> FitResult:
    """
    指定された範囲(indices)で線形回帰を行う。
    indicesがNoneの場合は全範囲を使用。
    """
    # 部分データの抽出
    if indices is not None:
        x_sub, y_sub = extract_subset(x, y, indices)
    else:
        x_sub, y_sub = x, y

    # データ点数が少なすぎる場合のガード
    if len(x_sub) < 2:
        return FitResult(0.0, 0.0, 0.0, False)

    # 線形回帰 (scipyを使用)
    slope, intercept, r_value, _, _ = stats.linregress(x_sub, y_sub)
    
    return FitResult(
        slope=slope,
        intercept=intercept,
        r2=r_value**2,
        is_valid=True
    )