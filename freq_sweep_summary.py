import argparse
import json
import os
from typing import Iterable

import numpy as np
import pandas as pd


OUTPUT_COLUMNS = ["sqrt_TW_freq", "theta", "theta_sigma", "amp", "amp_sigma"]


def load_logger_csv(path: str) -> pd.DataFrame:
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(path, comment="#", encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
    if last_err:
        raise last_err
    return pd.read_csv(path, comment="#")


def extract_metadata(path: str) -> dict:
    metadata: dict = {"meta_map": {}, "meta_items": [], "raw_meta_lines": [], "input_file": os.path.abspath(path)}
    last_err = None
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError as e:
            last_err = e
    if text is None:
        if last_err:
            raise last_err
        return metadata

    for line in text.splitlines():
        if not line.startswith("#META,"):
            continue
        metadata["raw_meta_lines"].append(line)
        body = line[len("#META,") :]
        parts = [p.strip() for p in body.split(",")]
        if len(parts) == 2:
            section, value = parts
            metadata["meta_map"][section] = value
            metadata["meta_items"].append({"section": section, "value": value})
        elif len(parts) >= 3:
            section, key = parts[0], parts[1]
            value = ",".join(parts[2:])
            metadata["meta_map"].setdefault(section, {})[key] = value
            metadata["meta_items"].append({"section": section, "key": key, "value": value})
    return metadata


def _circular_stats(rad_values: np.ndarray) -> tuple[float, float]:
    valid = np.isfinite(rad_values)
    vals = rad_values[valid]
    if vals.size == 0:
        return np.nan, np.nan

    unit = np.exp(1j * vals)
    mean_vec = np.mean(unit)
    mean_angle = float(np.angle(mean_vec))
    r = float(np.abs(mean_vec))
    r = min(max(r, 1e-12), 1.0)
    sigma = float(np.sqrt(-2.0 * np.log(r)))
    if abs(sigma) < 1e-15:
        sigma = 0.0
    elif sigma < 0.0:
        sigma = 0.0
    return mean_angle, sigma


def _cluster_frequency(values_hz: Iterable[float], tolerance_hz: float) -> np.ndarray:
    arr = np.asarray(list(values_hz), dtype=float)
    out = np.full(arr.shape, -1, dtype=int)
    valid_idx = np.where(np.isfinite(arr))[0]
    if valid_idx.size == 0:
        return out

    order = valid_idx[np.argsort(arr[valid_idx])]
    cluster_id = 0
    out[order[0]] = cluster_id
    anchor = arr[order[0]]

    for idx in order[1:]:
        if abs(arr[idx] - anchor) > tolerance_hz:
            cluster_id += 1
            anchor = arr[idx]
        out[idx] = cluster_id
    return out


def summarize_position(df_pos: pd.DataFrame, tolerance_hz: float) -> pd.DataFrame:
    df = df_pos.copy()
    df["freq_cluster"] = _cluster_frequency(df["LI_RefFreq_Hz"].to_numpy(dtype=float), tolerance_hz)
    df = df[df["freq_cluster"] >= 0]
    rows: list[dict] = []

    for _, part in df.groupby("freq_cluster", sort=True):
        freq_mean = float(np.nanmean(part["LI_RefFreq_Hz"]))
        amp_vals = pd.to_numeric(part["LI_Amp"], errors="coerce").to_numpy(dtype=float)
        theta_deg = pd.to_numeric(part["LI_Theta_deg"], errors="coerce").to_numpy(dtype=float)
        theta_rad = np.deg2rad(theta_deg)
        theta_mean, theta_sigma = _circular_stats(theta_rad)

        rows.append(
            {
                "sqrt_TW_freq": float(np.sqrt(max(freq_mean, 0.0))),
                "theta": theta_mean,
                "theta_sigma": theta_sigma,
                "amp": float(np.nanmean(amp_vals)),
                "amp_sigma": float(np.nanstd(amp_vals, ddof=0)),
            }
        )

    out = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    return out.sort_values("sqrt_TW_freq").reset_index(drop=True)


def build_position_key(df: pd.DataFrame) -> pd.Series:
    x = pd.to_numeric(df["Stage_X_um"], errors="coerce").round(6)
    y = pd.to_numeric(df["Stage_Y_um"], errors="coerce").round(6)
    z = pd.to_numeric(df["Stage_Z_um"], errors="coerce").round(6)
    return "x" + x.astype(str) + "_y" + y.astype(str) + "_z" + z.astype(str)


def _format_axis_value(value: float) -> str:
    if not np.isfinite(value):
        return "nan"
    rounded = round(float(value), 6)
    mag = abs(rounded)
    text = f"{mag:.6f}".rstrip("0").rstrip(".")
    if text == "":
        text = "0"
    text = text.replace(".", "p")
    prefix = "m" if rounded < 0 else ""
    return prefix + text


def build_position_filename(x: float, y: float, z: float) -> str:
    return f"x{_format_axis_value(x)},y{_format_axis_value(y)},z{_format_axis_value(z)}.csv"


def run(input_csv: str, output_dir: str, tolerance_hz: float) -> None:
    df = load_logger_csv(input_csv)
    base_metadata = extract_metadata(input_csv)
    required = {"Stage_X_um", "Stage_Y_um", "Stage_Z_um", "LI_Amp", "LI_Theta_deg", "LI_RefFreq_Hz"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"必要な列が不足しています: {missing}")

    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    df["position_key"] = build_position_key(df)
    used_filenames: dict[str, int] = {}

    for key, part in df.groupby("position_key", sort=False):
        x = float(pd.to_numeric(part["Stage_X_um"], errors="coerce").mean())
        y = float(pd.to_numeric(part["Stage_Y_um"], errors="coerce").mean())
        z = float(pd.to_numeric(part["Stage_Z_um"], errors="coerce").mean())
        out_name = build_position_filename(x, y, z)
        if out_name in used_filenames:
            used_filenames[out_name] += 1
            stem, ext = os.path.splitext(out_name)
            out_name = f"{stem}__{used_filenames[out_name]}{ext}"
        else:
            used_filenames[out_name] = 1
        out_csv_path = os.path.join(output_dir, out_name)
        summary = summarize_position(part, tolerance_hz=tolerance_hz)
        summary.to_csv(out_csv_path, index=False, columns=OUTPUT_COLUMNS)

    meta_summary = dict(base_metadata)
    meta_summary["freq_tolerance_hz"] = float(tolerance_hz)
    meta_summary["position_count"] = int(df["position_key"].nunique())
    meta_summary["output_dir"] = os.path.abspath(output_dir)
    meta_path = os.path.join(output_dir, "meta_summary.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_summary, f, indent=2, ensure_ascii=False)

    print(f"完了: {df['position_key'].nunique()} 位置を処理しました。")
    print(f"出力先: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="位置(x,y,z)ごとに周波数スイープを集約し、位相・振幅の統計CSVを出力します。"
    )
    parser.add_argument("input_csv", help="解析対象の data_logger CSV")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="出力先ディレクトリ（省略時: 入力CSVと同階層に *_pos_freq_summary を作成）",
    )
    parser.add_argument(
        "--freq-tolerance-hz",
        type=float,
        default=3.0,
        help="近接周波数を同一クラスタとして扱う閾値 [Hz]",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    in_path = os.path.abspath(args.input_csv)
    if not os.path.isfile(in_path):
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    out_dir = args.output_dir
    if out_dir is None:
        stem = os.path.splitext(os.path.basename(in_path))[0]
        out_dir = os.path.join(os.path.dirname(in_path), f"{stem}_pos_freq_summary")
    run(in_path, os.path.abspath(out_dir), args.freq_tolerance_hz)
