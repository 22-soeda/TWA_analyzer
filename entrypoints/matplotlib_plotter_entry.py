import glob
import os
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.widgets import SpanSelector
import numpy as np

from .common_io import (
    apply_tick_aligned_limits,
    load_json,
    read_xy_dataframe,
    resolve_axis_label,
    resolve_column_name,
)
from .contracts import PlotterRequest, PlotterResponse


class InteractiveFitter:
    def __init__(self, x, y, xlabel, ylabel, title_prefix, output_dir, output_base_name):
        self.x = np.array(x)
        self.y = np.array(y)
        self.output_dir = output_dir
        self.output_base_name = output_base_name
        self.fit_params = None

        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.ax.set_title(title_prefix)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(False)

        self.ax.scatter(self.x, self.y, color="blue", alpha=0.6, label="Data")
        self.highlight = self.ax.scatter([], [], facecolors="none", edgecolors="red", linewidths=1.5, label="Selected")
        self.line, = self.ax.plot([], [], "r-", linewidth=2, label="Fit")
        self.text = self.ax.text(0.5, 1.02, "", transform=self.ax.transAxes, ha="center", va="bottom")
        self.ax.legend(loc="upper right")
        apply_tick_aligned_limits(self.ax, self.x, self.y)

        self.selector = SpanSelector(
            self.ax,
            self.on_select,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.2, facecolor="red"),
            interactive=True,
            drag_from_anywhere=True,
        )
        self.fig.canvas.mpl_connect("close_event", self.on_close)

    def on_select(self, xmin, xmax):
        idx = np.where((self.x >= xmin) & (self.x <= xmax))[0]
        if len(idx) < 2:
            return
        x_fit = self.x[idx]
        y_fit = self.y[idx]
        slope, intercept = np.polyfit(x_fit, y_fit, 1)
        self.fit_params = (slope, intercept)
        self.highlight.set_offsets(np.c_[x_fit, y_fit])
        x_line = np.linspace(np.min(x_fit), np.max(x_fit), 100)
        self.line.set_data(x_line, slope * x_line + intercept)
        self.text.set_text(f"Fit Result: y = {slope:.4f}x + {intercept:.4f}")
        self.fig.canvas.draw_idle()

    def _get_output_path(self):
        base, _ = os.path.splitext(self.output_base_name)
        n = 1
        while True:
            path = os.path.join(self.output_dir, f"{base}_fit_{n}.png")
            if not os.path.exists(path):
                return path
            n += 1

    def on_close(self, _):
        path = self._get_output_path()
        self.fig.savefig(path, bbox_inches="tight")
        print(f"Saved: {path}")


def _find_config_path(target_dir: str, explicit_path: Optional[str]) -> Optional[str]:
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path
    candidates = glob.glob(os.path.join(target_dir, "*.json"))
    if not candidates:
        return None
    return candidates[0]


def _resolve_headers(config: Dict, columns: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    headers = config.get("headers", {}) if isinstance(config, dict) else {}
    xh = resolve_column_name(columns, headers.get("x"), 0)
    yh = resolve_column_name(columns, headers.get("y"), 1)
    return xh, yh, headers.get("y_upper"), headers.get("y_lower")


def _plot_with_config(
    target_dir: str,
    config: Dict,
    include_errorbars: bool,
) -> PlotterResponse:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.grid(False)

    plots = config.get("plots", []) if isinstance(config, dict) else []
    xlabel_cfg = config.get("xlabel") if isinstance(config, dict) else None
    ylabel_cfg = config.get("ylabel") if isinstance(config, dict) else None

    output_files: List[str] = []
    used_labels: List[str] = []
    warnings: List[str] = []
    plotted = 0

    all_x = []
    all_y = []
    xlabel = "X Axis"
    ylabel = "Y Axis"

    for item in plots:
        csv_name = item.get("csv_file")
        if not csv_name:
            continue
        legend = item.get("legend", csv_name)
        shift_x = float(item.get("shift_z", 0.0))
        shift_y = float(item.get("shift_y", 0.0))
        csv_path = os.path.join(target_dir, csv_name)
        if not os.path.exists(csv_path):
            warnings.append(f"missing file: {csv_name}")
            continue
        try:
            preview_df = pd.read_csv(csv_path)
            xh, yh, y_upper_h, y_lower_h = _resolve_headers(config, preview_df.columns.tolist())
            x_data, y_data, resolved_x, resolved_y = read_xy_dataframe(csv_path, xh, yh, shift_x, shift_y)
            if len(x_data) == 0:
                warnings.append(f"empty numeric data: {csv_name}")
                continue
            xlabel = resolve_axis_label(xlabel_cfg, resolved_x, "X Axis")
            ylabel = resolve_axis_label(ylabel_cfg, resolved_y, "Y Axis")

            if include_errorbars and y_upper_h in preview_df.columns and y_lower_h in preview_df.columns:
                df_num = preview_df.apply(pd.to_numeric, errors="coerce")
                valid = df_num[resolved_x].notna() & df_num[resolved_y].notna()
                dvalid = df_num[valid]
                y_center = dvalid[resolved_y] + shift_y
                err_lo = y_center - (dvalid[y_lower_h] + shift_y)
                err_up = (dvalid[y_upper_h] + shift_y) - y_center
                ax.errorbar(x_data, y_data, yerr=[err_lo, err_up], fmt="o", label=legend, linestyle="none")
            else:
                ax.scatter(x_data, y_data, label=legend, s=30, marker="o")

            all_x.extend(x_data.tolist())
            all_y.extend(y_data.tolist())
            used_labels.append(f"{resolved_x}->{xlabel}, {resolved_y}->{ylabel}")
            plotted += 1
        except Exception as e:
            warnings.append(f"{csv_name}: {e}")

    if plotted == 0:
        plt.close(fig)
        return PlotterResponse([], 0, used_labels, warnings)

    ax.legend()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    apply_tick_aligned_limits(ax, np.array(all_x), np.array(all_y))

    filename = "plot_output_with_errorbars.png" if include_errorbars else "plot_output.png"
    output_path = os.path.join(target_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    output_files.append(output_path)
    return PlotterResponse(output_files, plotted, used_labels, warnings)


def _run_interactive_fit(target_dir: str, csv_file: str, config: Optional[Dict]) -> Optional[str]:
    csv_path = csv_file if os.path.isabs(csv_file) else os.path.join(target_dir, csv_file)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    xh, yh, _, _ = _resolve_headers(config or {}, df.columns.tolist())
    x_data, y_data, resolved_x, resolved_y = read_xy_dataframe(csv_path, xh, yh)
    xlabel = resolve_axis_label((config or {}).get("xlabel"), resolved_x, "X")
    ylabel = resolve_axis_label((config or {}).get("ylabel"), resolved_y, "Y")
    title = os.path.basename(csv_path)

    fitter = InteractiveFitter(x_data.values, y_data.values, xlabel, ylabel, title, target_dir, os.path.basename(csv_path))
    plt.show()
    return "interactive_fit_saved_on_close"


def run_matplotlib_plotter(request: PlotterRequest) -> PlotterResponse:
    config_path = _find_config_path(request.target_dir, request.config_path)
    config = load_json(config_path) if config_path else {}

    if request.interactive_fit_csv:
        marker = _run_interactive_fit(request.target_dir, request.interactive_fit_csv, config)
        return PlotterResponse([marker] if marker else [], 1 if marker else 0, [], [])

    return _plot_with_config(request.target_dir, config, request.include_errorbars)

