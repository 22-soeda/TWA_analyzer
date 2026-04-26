import glob
import json
import os
from typing import Dict, List, Optional, Tuple

import matplotlib.ticker as ticker
import numpy as np
import pandas as pd


def find_json_files(target_dir: str, filename: str) -> List[str]:
    pattern = os.path.join(target_dir, "**", filename)
    return glob.glob(pattern, recursive=True)


def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def read_xy_dataframe(
    csv_path: str,
    x_header: Optional[str] = None,
    y_header: Optional[str] = None,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
) -> Tuple[pd.Series, pd.Series, str, str]:
    df = pd.read_csv(csv_path)
    if df.shape[1] < 2:
        raise ValueError("2列以上のCSVが必要です。")

    resolved_x = resolve_column_name(df.columns.tolist(), x_header, fallback_idx=0)
    resolved_y = resolve_column_name(df.columns.tolist(), y_header, fallback_idx=1)

    x_raw = pd.to_numeric(df[resolved_x], errors="coerce")
    y_raw = pd.to_numeric(df[resolved_y], errors="coerce")
    valid = x_raw.notna() & y_raw.notna()

    return x_raw[valid] + shift_x, y_raw[valid] + shift_y, resolved_x, resolved_y


def resolve_column_name(headers: List[str], preferred: Optional[str], fallback_idx: int) -> str:
    if preferred and preferred in headers:
        return preferred

    if headers:
        normalized = [h.strip().lower() for h in headers]
        if fallback_idx == 0:
            for candidate in ("x", "z", "freq", "sqrt_tw_freq", "sqrt_f"):
                if candidate in normalized:
                    return headers[normalized.index(candidate)]
        if fallback_idx == 1:
            for candidate in ("y", "alpha", "theta", "amp", "thermal_diffusivity"):
                if candidate in normalized:
                    return headers[normalized.index(candidate)]

    return headers[fallback_idx]


def resolve_axis_label(
    config_label: Optional[str],
    resolved_header: str,
    default_label: str,
) -> str:
    if config_label:
        return config_label
    if resolved_header:
        return resolved_header
    return default_label


def compute_robust_limits(values: np.ndarray, margin_ratio: float = 0.1) -> Tuple[float, float]:
    if len(values) == 0:
        return 0.0, 1.0
    vmin = float(np.nanmin(values))
    vmax = float(np.nanmax(values))
    if vmin == vmax:
        span = abs(vmin) * margin_ratio if vmin != 0 else 1.0
        return vmin - span, vmax + span

    q1, q99 = np.nanpercentile(values, [1, 99])
    trimmed_min = min(vmin, float(q1))
    trimmed_max = max(vmax, float(q99))
    span = trimmed_max - trimmed_min
    return trimmed_min - span * margin_ratio, trimmed_max + span * margin_ratio


def apply_tick_aligned_limits(ax, x_data: np.ndarray, y_data: np.ndarray) -> None:
    x0, x1 = compute_robust_limits(x_data)
    y0, y1 = compute_robust_limits(y_data)

    locator = ticker.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10])
    x_ticks = locator.tick_values(x0, x1)
    y_ticks = locator.tick_values(y0, y1)

    if len(x_ticks) >= 2:
        ax.set_xlim(x_ticks[0], x_ticks[-1])
        ax.set_xticks(x_ticks)
    if len(y_ticks) >= 2:
        ax.set_ylim(y_ticks[0], y_ticks[-1])
        ax.set_yticks(y_ticks)

