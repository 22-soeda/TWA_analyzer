import pandas as pd
import io
import os
import numpy as np
from typing import Dict, Tuple

try:
    from .datamodels import RawData
except ImportError:
    from datamodels import RawData

# configから位相列名を取得するためのインポート
try:
    import config
    PHASE_COL_NAME = config.columns.PHASE
except ImportError:
    PHASE_COL_NAME = "theta"


def _canonical_twa_column_names() -> Tuple[str, str, str, str]:
    """解析パイプラインが参照する列名（config が無い場合は従来の既定）。"""
    try:
        c = config.columns
        return c.SQRT_FREQUENCY, c.AMPLITUDE, c.PHASE, c.Z_POS
    except ImportError:
        return "sqrt_TW_freq", "amp", "theta", "z_pos"


def _canonical_twa_position_keys() -> Tuple[str, str, str]:
    """解析結果に反映する座標メタデータのキー名。"""
    try:
        c = config.columns
        return c.X_POS, c.Y_POS, c.Z_POS
    except ImportError:
        return "x_pos", "y_pos", "z_pos"


def _load_csv_table(filepath: str) -> pd.DataFrame:
    """#META 行付きのデータロガー CSV 等を読み込む（# で始まる行はスキップ）。"""
    last_err: Exception | None = None
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(filepath, comment="#", encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
    if last_err:
        raise last_err
    return pd.read_csv(filepath, comment="#")


def _load_csv_meta(filepath: str) -> Dict[str, float]:
    """CSV先頭の #META 行から座標メタデータを読み込む。"""
    x_key, y_key, z_key = _canonical_twa_position_keys()
    key_map = {"x_pos": x_key, "y_pos": y_key, "z_pos": z_key}
    metadata: Dict[str, float] = {}
    last_err: Exception | None = None
    lines = None
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError as e:
            last_err = e
    if lines is None:
        if last_err:
            raise last_err
        return metadata

    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("#META,"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 4:
            meta_key = key_map.get(parts[2], parts[2])
            try:
                metadata[meta_key] = float(parts[3])
            except ValueError:
                pass
    return metadata


def _ensure_twa_canonical_columns(df: pd.DataFrame, metadata: Dict[str, float]) -> None:
    """
    TWA 解析用の列（sqrt_TW_freq, amp, theta）が無い場合、
    data_logger 形式（LI_Amp, LI_Theta_deg, LI_RefFreq_Hz / FG_Freq_Hz）から生成する。
    周波数 f は LI_RefFreq_Hz を優先し、列が無い場合のみ FG_Freq_Hz を使用する。
    既に canonical 列が揃っていれば何もしない。
    """
    sqrt_n, amp_n, phase_n, z_key = _canonical_twa_column_names()
    x_key, y_key, _ = _canonical_twa_position_keys()
    if sqrt_n in df.columns and amp_n in df.columns and phase_n in df.columns:
        return

    if "LI_Amp" not in df.columns or "LI_Theta_deg" not in df.columns:
        raise ValueError(
            "TWA 用の列が見つかりません。"
            f" 必要な列のいずれか: ({sqrt_n}, {amp_n}, {phase_n}) または "
            "(LI_Amp, LI_Theta_deg, LI_RefFreq_Hz または FG_Freq_Hz)。"
            f" 実際の列: {list(df.columns)}"
        )

    if "LI_RefFreq_Hz" in df.columns:
        freq_col = "LI_RefFreq_Hz"
    elif "FG_Freq_Hz" in df.columns:
        freq_col = "FG_Freq_Hz"
    else:
        raise ValueError(
            "周波数列がありません。LI_RefFreq_Hz または FG_Freq_Hz が必要です。"
            f" 実際の列: {list(df.columns)}"
        )

    f_hz = pd.to_numeric(df[freq_col], errors="coerce").to_numpy(dtype=float)
    f_hz = np.where(np.isfinite(f_hz), f_hz, np.nan)
    f_hz = np.clip(f_hz, 0.0, None)
    df[sqrt_n] = np.sqrt(f_hz)
    df[amp_n] = pd.to_numeric(df["LI_Amp"], errors="coerce")
    theta_deg = pd.to_numeric(df["LI_Theta_deg"], errors="coerce").to_numpy(dtype=float)
    df[phase_n] = np.deg2rad(theta_deg)

    # 座標フラグ列（x_pos/y_pos/z_pos）を優先し、無ければ Stage_*_um から補完
    for meta_key, preferred_col, fallback_col in (
        (x_key, x_key, "Stage_X_um"),
        (y_key, y_key, "Stage_Y_um"),
        (z_key, z_key, "Stage_Z_um"),
    ):
        if meta_key in metadata:
            continue
        source_col = preferred_col if preferred_col in df.columns else fallback_col
        if source_col in df.columns:
            vals = pd.to_numeric(df[source_col], errors="coerce")
            if vals.notna().any():
                metadata[meta_key] = float(vals.mean())


def unwrap_phase_custom(phase_data: np.ndarray, period: float = np.pi, threshold: float = 3.0) -> np.ndarray:
    """
    位相アンラップ処理（ベクトル化済み）

    隣接点間の差分が threshold (デフォルト3.0) を超えた場合、
    period (デフォルトpi) の整数倍を加減算して連続性を保つように補正します。

    Parameters:
      phase_data: 位相データの1次元配列
      period: 補正する周期（ユーザー要件により pi をデフォルト設定）
      threshold: 補正判定を行う差分の閾値（ユーザー要件により 3.0 をデフォルト設定）
                 ※通常のunwrapは period/2 ですが、急激な物理変化を許容するため高めに設定可能です
    """
    diff = np.diff(phase_data)

    mask = np.abs(diff) > threshold

    k = np.round(diff / period) * mask

    correction = -k * period

    cumulative_correction = np.cumsum(correction)

    unwrapped_phase = phase_data.copy()
    unwrapped_phase[1:] += cumulative_correction

    return unwrapped_phase


def adjust_phase_continuity(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    DataFrame内の指定列に対して位相アンラップを適用
    """
    if col_name not in df.columns:
        return df

    phase_values = df[col_name].values

    new_phase = unwrap_phase_custom(phase_values, period=np.pi, threshold=3.0)

    df[col_name] = new_phase
    return df


def load_from_text(filepath: str, sep: str = "\t") -> RawData:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = _load_csv_table(filepath)
        df.columns = [c.strip() for c in df.columns]
        metadata: Dict[str, float] = _load_csv_meta(filepath)
        _ensure_twa_canonical_columns(df, metadata)
        if PHASE_COL_NAME in df.columns:
            df = adjust_phase_continuity(df, PHASE_COL_NAME)
        return RawData(df=df, metadata=metadata, filepath=filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="cp932") as f:
            lines = f.readlines()

    separator_idx = -1
    for i, line in enumerate(lines):
        if "sample information" in line:
            separator_idx = i
            break

    data_lines = lines[:separator_idx] if separator_idx != -1 else lines
    data_str = "".join(data_lines)
    df = pd.read_csv(io.StringIO(data_str), sep=sep)

    df.columns = [c.strip() for c in df.columns]

    if len(df.columns) > 1:
        common_prefix = os.path.commonprefix(list(df.columns))

        if common_prefix and len(common_prefix) < min(len(c) for c in df.columns):
            new_columns = []
            for col in df.columns:
                new_col = col.replace(common_prefix, "", 1)
                new_columns.append(new_col)

            df.columns = new_columns

    metadata: Dict[str, float] = {}
    if separator_idx != -1:
        meta_lines = lines[separator_idx + 1 :]
        for line in meta_lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(sep)

            if len(parts) < 2:
                parts = line.split(None, 1)

            if len(parts) >= 2:
                key = parts[0].strip()
                val_str = parts[1].strip()

                try:
                    val = float(val_str)
                    metadata[key] = val
                except ValueError:
                    pass

    _ensure_twa_canonical_columns(df, metadata)

    if PHASE_COL_NAME in df.columns:
        df = adjust_phase_continuity(df, PHASE_COL_NAME)

    return RawData(df=df, metadata=metadata, filepath=filepath)


# ---------------------------------------------------------
# 動作確認用コード
# ---------------------------------------------------------

if __name__ == "__main__":
    print("==========================================")
    print("   RawData Parser : Interactive Mode")
    print("==========================================")

    test_phase = np.array([0.1, 0.2, 3.4, 3.5, 0.3, -3.0])
    print("Test Phase Raw:", test_phase)
    unwrapped = unwrap_phase_custom(test_phase, period=np.pi, threshold=3.0)
    print("Unwrapped:     ", unwrapped)
    print("-" * 50)

    print("解析したいテキストファイルのパスを入力してください。")

    while True:
        try:
            user_input = input("File Path > ").strip()
            if user_input.lower() in ["q", "exit", "quit"]:
                break
            if not user_input:
                continue

            file_path = user_input.strip('"').strip("'")

            if not os.path.exists(file_path):
                print(f"[Error] ファイルが見つかりません: {file_path}")
                continue

            print(f"\nLoading: {file_path} ...")
            result = load_from_text(file_path, sep="\t")

            print("-" * 50)
            print("■ データプレビュー (先頭5行)")
            print(result.df.head())

            if PHASE_COL_NAME in result.df.columns:
                print(f"\n■ 位相データ ({PHASE_COL_NAME}) の一部:")
                print(result.df[PHASE_COL_NAME].values[:10])

        except Exception as e:
            print(f"\n[Error] {e}")
