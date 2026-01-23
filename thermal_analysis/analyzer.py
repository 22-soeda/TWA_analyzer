from typing import List, Optional
import numpy as np
from .datamodels import RawData, AnalysisResult
from . import fitting, physics

def run_analysis(raw_data: RawData, config, used_indices: Optional[List[int]] = None) -> AnalysisResult:
    """
    生データと指定されたインデックス（範囲）に基づいて解析を実行し、
    メタデータ等を含めた完全なAnalysisResultオブジェクトを生成して返す。
    
    used_indicesがNoneの場合は、全データを使用する。
    """
    # データ抽出
    x_data = raw_data.df[config.COL_FREQ_SQRT].values
    amp_data = raw_data.df[config.COL_AMP].values
    phase_data = raw_data.df[config.COL_PHASE].values
    y_amp_log = np.log(amp_data)
    
    thickness = raw_data.metadata.get("試料厚", config.DEFAULT_THICKNESS_UM)

    # インデックスの決定（指定がなければ全範囲）
    if used_indices is None:
        used_indices = list(range(len(x_data)))
    
    # 解析可能な点数かチェック
    if len(used_indices) < 2:
        # 計算不可の場合は空に近い結果を返す（または例外）
        return AnalysisResult(
            filename=raw_data.filepath,
            thickness_um=thickness,
            used_indices=[],
            freq_range_min=0, freq_range_max=0,
            kd_min=0, kd_max=0
        )

    # 部分データの抽出
    x_sub = x_data[used_indices]
    
    # 1. フィッティング実行
    fit_phase = fitting.linear_regression_subset(x_data, phase_data, used_indices)
    fit_amp = fitting.linear_regression_subset(x_data, y_amp_log, used_indices)

    # 2. 物理量計算
    alpha_phase = physics.calculate_alpha_from_slope(fit_phase.slope, thickness)
    alpha_amp = physics.calculate_alpha_from_slope(fit_amp.slope, thickness)

    # kd計算 (Phase由来のAlphaを使用)
    # x = sqrt(f) なので f = x^2
    freq_sub = x_sub ** 2
    kd_values = physics.calculate_kd(freq_sub, alpha_phase, thickness)
    kd_min = float(np.min(kd_values)) if len(kd_values) > 0 else 0.0
    kd_max = float(np.max(kd_values)) if len(kd_values) > 0 else 0.0

    # 比率計算
    alpha_ratio = 0.0
    if alpha_amp > 0 and alpha_phase > 0:
        alpha_ratio = min(alpha_amp, alpha_phase) / max(alpha_amp, alpha_phase)

    # 3. メタデータ抽出 (configのキー設定に従う)
    meta = raw_data.metadata
    x_pos = meta.get(config.KEY_X_POS)
    y_pos = meta.get(config.KEY_Y_POS)
    z_pos = meta.get(config.KEY_Z_POS)

    # 結果オブジェクト生成
    return AnalysisResult(
        filename=raw_data.filepath,
        thickness_um=thickness,
        
        alpha_amp=alpha_amp,
        r2_amp=fit_amp.r2,
        slope_amp=fit_amp.slope,
        intercept_amp=fit_amp.intercept,
        
        alpha_phase=alpha_phase,
        r2_phase=fit_phase.r2,
        slope_phase=fit_phase.slope,
        intercept_phase=fit_phase.intercept,
        
        alpha_ratio=alpha_ratio,
        
        x_position=x_pos,
        y_position=y_pos,
        z_position=z_pos,
        
        used_indices=used_indices,
        freq_range_min=float(np.min(x_sub)),
        freq_range_max=float(np.max(x_sub)),
        kd_min=kd_min,
        kd_max=kd_max
    )