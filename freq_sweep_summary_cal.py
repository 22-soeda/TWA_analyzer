import os

import matplotlib.pyplot as plt
import pandas as pd

from config import AppConfig
from freq_sweep_summary import build_position_filename, build_position_key, load_logger_csv, run


def _resolve_elapsed_seconds(df: pd.DataFrame) -> pd.Series:
    """経過時間列を解決し、先頭を 0 秒に正規化して返す。"""
    if "Elapsed_s" in df.columns:
        t = pd.to_numeric(df["Elapsed_s"], errors="coerce")
        if t.notna().any():
            return t - float(t.dropna().iloc[0])
    if "Sys_Timestamp" in df.columns:
        t = pd.to_numeric(df["Sys_Timestamp"], errors="coerce")
        if t.notna().any():
            return t - float(t.dropna().iloc[0])
    raise ValueError("時間列が見つかりません。Elapsed_s または Sys_Timestamp が必要です。")


def _save_time_series_plots(input_csv: str, output_dir: str) -> None:
    """
    各位置の時系列データについて、以下2種類を保存する。
    - 周波数 + 位相差 vs 経過時間
    - 周波数 + 振幅   vs 経過時間
    """
    df = load_logger_csv(input_csv).copy()
    required = {"Stage_X_um", "Stage_Y_um", "Stage_Z_um", "LI_RefFreq_Hz", "LI_Theta_deg", "LI_Amp"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"時系列グラフに必要な列が不足しています: {missing}")

    elapsed = _resolve_elapsed_seconds(df)
    df["elapsed_s_plot"] = elapsed
    df["position_key"] = build_position_key(df)

    plot_root = os.path.join(output_dir, "time_series_plots")
    os.makedirs(plot_root, exist_ok=True)

    for _, part in df.groupby("position_key", sort=False):
        x = float(pd.to_numeric(part["Stage_X_um"], errors="coerce").mean())
        y = float(pd.to_numeric(part["Stage_Y_um"], errors="coerce").mean())
        z = float(pd.to_numeric(part["Stage_Z_um"], errors="coerce").mean())
        pos_name = os.path.splitext(build_position_filename(x, y, z))[0]
        pos_dir = os.path.join(plot_root, pos_name)
        os.makedirs(pos_dir, exist_ok=True)

        t = pd.to_numeric(part["elapsed_s_plot"], errors="coerce")
        freq = pd.to_numeric(part["LI_RefFreq_Hz"], errors="coerce")
        phase_deg = pd.to_numeric(part["LI_Theta_deg"], errors="coerce")
        amp = pd.to_numeric(part["LI_Amp"], errors="coerce")

        # 1) 経過時間 vs (周波数, 位相差)
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.scatter(t, freq, color="tab:blue", s=12, alpha=0.8, label="Frequency [Hz]")
        ax1.set_xlabel("Elapsed Time [s]")
        ax1.set_ylabel("Frequency [Hz]", color="tab:blue")
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax1.grid(True, alpha=0.3)

        ax1b = ax1.twinx()
        ax1b.scatter(t, phase_deg, color="tab:orange", s=12, alpha=0.8, label="Phase Diff [deg]")
        ax1b.set_ylabel("Phase Diff [deg]", color="tab:orange")
        ax1b.tick_params(axis="y", labelcolor="tab:orange")
        ax1.set_title(f"{pos_name} : Frequency & Phase vs Time")
        fig1.tight_layout()
        fig1.savefig(os.path.join(pos_dir, "time_vs_frequency_phase.png"), dpi=150)
        plt.close(fig1)

        # 2) 経過時間 vs (周波数, 振幅)
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.scatter(t, freq, color="tab:blue", s=12, alpha=0.8, label="Frequency [Hz]")
        ax2.set_xlabel("Elapsed Time [s]")
        ax2.set_ylabel("Frequency [Hz]", color="tab:blue")
        ax2.tick_params(axis="y", labelcolor="tab:blue")
        ax2.grid(True, alpha=0.3)

        ax2b = ax2.twinx()
        ax2b.scatter(t, amp, color="tab:green", s=12, alpha=0.8, label="Amplitude")
        ax2b.set_ylabel("Amplitude", color="tab:green")
        ax2b.tick_params(axis="y", labelcolor="tab:green")
        ax2.set_title(f"{pos_name} : Frequency & Amplitude vs Time")
        fig2.tight_layout()
        fig2.savefig(os.path.join(pos_dir, "time_vs_frequency_amplitude.png"), dpi=150)
        plt.close(fig2)

    print(f"時系列グラフを保存しました: {plot_root}")


def main() -> None:
    print("==========================================")
    print(" Freq Sweep Summary : Interactive Mode")
    print("==========================================")

    default_input = os.path.join(
        os.getcwd(),
        "data_raw",
        "z_freq_sweep_test01_20260421_121456",
        "data_1.csv",
    )
    in_input = input(f"Input Path (Default: {default_input}) > ").strip().strip('"').strip("'")
    input_csv = in_input if in_input else default_input
    input_csv = os.path.abspath(input_csv)

    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_csv}")

    stem = os.path.splitext(os.path.basename(input_csv))[0]
    default_output = os.path.join(AppConfig.OUTPUT_DIR, f"{stem}_pos_freq_summary")
    out_input = input(f"Output Path (Default: {default_output}) > ").strip().strip('"').strip("'")
    output_dir = out_input if out_input else default_output

    tol_input = input("Freq Tolerance Hz (Default: 3.0) > ").strip()
    freq_tolerance_hz = float(tol_input) if tol_input else 3.0

    run(
        input_csv=input_csv,
        output_dir=os.path.abspath(output_dir),
        tolerance_hz=freq_tolerance_hz,
    )
    _save_time_series_plots(
        input_csv=input_csv,
        output_dir=os.path.abspath(output_dir),
    )


if __name__ == "__main__":
    main()
