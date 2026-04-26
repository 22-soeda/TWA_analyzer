import os
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .common_io import apply_tick_aligned_limits, find_json_files, load_json
from .contracts import DiffusivitySummaryRequest, DiffusivitySummaryResponse


def _scatter_plot(
    x: pd.Series,
    y: pd.Series,
    save_path: str,
    xlabel: str,
    ylabel: str,
    color: str = "blue",
) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(x, y, marker="o", linestyle="None", color=color)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(False)
    apply_tick_aligned_limits(ax, x.values, y.values)
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def _build_pos_summary(target_dir: str) -> DiffusivitySummaryResponse:
    result_files = find_json_files(target_dir, "results.json")
    rows: List[Dict] = []
    warnings: List[str] = []

    for path in result_files:
        try:
            res = load_json(path)
            z = res.get("z_position")
            alpha_phase = res.get("alpha_phase")
            alpha_ratio = res.get("alpha_ratio")
            if z is None or alpha_phase is None:
                continue
            rows.append(
                {
                    "id": os.path.basename(os.path.dirname(path)),
                    "z_position": float(z),
                    "alpha_phase": float(alpha_phase),
                    "alpha_ratio": float(alpha_ratio) if alpha_ratio is not None else 0.0,
                }
            )
        except Exception as e:
            warnings.append(f"{path}: {e}")

    if not rows:
        return DiffusivitySummaryResponse([], 0, warnings)

    df = pd.DataFrame(rows).sort_values(by="z_position")
    summary_json_path = os.path.join(target_dir, "summary_results.json")
    summary_csv_path = os.path.join(target_dir, "summary_results.csv")
    df.to_json(summary_json_path, orient="records", indent=4)
    df[["z_position", "alpha_phase"]].rename(columns={"z_position": "z", "alpha_phase": "thermal_diffusivity"}).to_csv(
        summary_csv_path, index=False, encoding="utf-8"
    )

    phase_plot = os.path.join(target_dir, "summary_pos_alpha.png")
    ratio_plot = os.path.join(target_dir, "summary_pos_ratio.png")
    _scatter_plot(df["z_position"], df["alpha_phase"], phase_plot, "Z Position [um]", r"Thermal Diffusivity [m$^2$/s]", "orange")
    _scatter_plot(df["z_position"], df["alpha_ratio"], ratio_plot, "Z Position [um]", "Alpha Ratio", "green")

    return DiffusivitySummaryResponse([summary_json_path, summary_csv_path, phase_plot, ratio_plot], len(df), warnings)


def _build_thickness_summary(target_dir: str) -> DiffusivitySummaryResponse:
    result_files = find_json_files(target_dir, "results.json")
    rows = []
    warnings: List[str] = []
    for path in result_files:
        try:
            res = load_json(path)
            z = res.get("z_position")
            thickness = res.get("thickness_um")
            if z is None or thickness is None:
                continue
            rows.append(
                {
                    "id": os.path.basename(os.path.dirname(path)),
                    "z_position": float(z),
                    "thickness_um": float(thickness),
                }
            )
        except Exception as e:
            warnings.append(f"{path}: {e}")
    if not rows:
        return DiffusivitySummaryResponse([], 0, warnings)

    df = pd.DataFrame(rows).sort_values(by="z_position")
    summary_path = os.path.join(target_dir, "summary_thickness.json")
    fig_path = os.path.join(target_dir, "summary_z_vs_thickness.png")
    df.to_json(summary_path, orient="records", indent=4)
    _scatter_plot(df["z_position"], df["thickness_um"], fig_path, "Z Position [um]", "Sample Thickness [um]", "blue")
    return DiffusivitySummaryResponse([summary_path, fig_path], len(df), warnings)


def _build_confidence_summary(target_dir: str, confidence_percent: float) -> DiffusivitySummaryResponse:
    warnings: List[str] = []
    rows = []
    conf_label = int(confidence_percent)
    for item in os.listdir(target_dir):
        sub_dir = os.path.join(target_dir, item)
        input_path = os.path.join(sub_dir, "input_data.json")
        results_path = os.path.join(sub_dir, "results.json")
        if not os.path.isdir(sub_dir) or not os.path.exists(input_path) or not os.path.exists(results_path):
            continue
        try:
            input_data = load_json(input_path)
            results_data = load_json(results_path)
            used_indices = results_data.get("used_indices", [])
            thickness_m = float(results_data.get("thickness_um", 0.0)) * 1e-6
            z_position = results_data.get("z_position")
            df_raw = pd.DataFrame(input_data["dataframe"]["data"], columns=input_data["dataframe"]["columns"])
            df_used = df_raw.iloc[used_indices]
            x = df_used["sqrt_TW_freq"].values
            y = df_used["theta"].values
            if len(x) < 3:
                continue
            slope, _, r_val, _, std_err = stats.linregress(x, y)
            q = 0.5 + (confidence_percent / 200.0)
            t_crit = stats.t.ppf(q, len(x) - 2)
            delta_b = t_crit * std_err
            b_abs = abs(slope)
            b_min = b_abs - delta_b
            b_max = b_abs + delta_b
            alpha = np.pi * (thickness_m / b_abs) ** 2
            alpha_upper = np.pi * (thickness_m / b_min) ** 2 if b_min > 0 else float("inf")
            alpha_lower = np.pi * (thickness_m / b_max) ** 2
            rows.append(
                {
                    "z_position": z_position,
                    "alpha": alpha,
                    f"alpha_upper_{conf_label}%": alpha_upper,
                    f"alpha_lower_{conf_label}%": alpha_lower,
                    "confidence_percent": confidence_percent,
                    "slope": slope,
                    "slope_err": std_err,
                    "R2": r_val**2,
                }
            )
        except Exception as e:
            warnings.append(f"{sub_dir}: {e}")

    if not rows:
        return DiffusivitySummaryResponse([], 0, warnings)

    df = pd.DataFrame(rows).sort_values("z_position").reset_index(drop=True)
    output_path = os.path.join(target_dir, "thermal_diffusivity_summary.csv")
    df.to_csv(output_path, index=False)
    return DiffusivitySummaryResponse([output_path], len(df), warnings)


def run_diffusivity_summary(request: DiffusivitySummaryRequest) -> DiffusivitySummaryResponse:
    summary_type = request.summary_type.lower()
    if summary_type == "position":
        return _build_pos_summary(request.target_dir)
    if summary_type == "thickness":
        return _build_thickness_summary(request.target_dir)
    if summary_type == "confidence":
        return _build_confidence_summary(request.target_dir, request.confidence_percent)
    raise ValueError(f"Unknown summary type: {request.summary_type}")

