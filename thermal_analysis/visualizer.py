import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.ticker as ticker
from typing import Optional, List
from .datamodels import RawData, AnalysisResult

def _set_smart_limits(ax, x_data, y_data, margin=0.1):
    """
    データ範囲に基づいて、グリッド線がちょうど上限下限に来るように設定するヘルパー関数
    """
    if len(x_data) == 0 or len(y_data) == 0:
        return

    def get_nice_ticks(data_min, data_max, margin_ratio):
        span = data_max - data_min
        if span == 0:
            span = 1.0
        
        target_min = data_min - span * margin_ratio
        target_max = data_max + span * margin_ratio
        
        locator = ticker.MaxNLocator(nbins='auto', steps=[1, 2, 2.5, 5, 10])
        ticks = locator.tick_values(target_min, target_max)
        
        if len(ticks) > 1:
            step = ticks[1] - ticks[0]
        else:
            step = span * 0.1 if span > 0 else 0.1

        while len(ticks) > 0 and ticks[0] > data_min:
            ticks = np.insert(ticks, 0, ticks[0] - step)
        while len(ticks) > 0 and ticks[-1] < data_max:
            ticks = np.append(ticks, ticks[-1] + step)
            
        return ticks

    # X軸設定
    x_min, x_max = np.min(x_data), np.max(x_data)
    x_ticks = get_nice_ticks(x_min, x_max, margin)
    if len(x_ticks) >= 2:
        ax.set_xlim(x_ticks[0], x_ticks[-1])
        ax.set_xticks(x_ticks)

    # Y軸設定
    y_min, y_max = np.min(y_data), np.max(y_data)
    y_ticks = get_nice_ticks(y_min, y_max, margin)
    if len(y_ticks) >= 2:
        ax.set_ylim(y_ticks[0], y_ticks[-1])
        ax.set_yticks(y_ticks)

def _generic_plot_and_save(
    x_all: np.ndarray,
    y_all: np.ndarray,
    output_path: str,
    xlabel: str,
    ylabel: str,
    title: str,
    used_indices: Optional[List[int]] = None,
    slope: Optional[float] = None,
    intercept: Optional[float] = None,
    data_label_valid: str = "Used Data",
    color_valid: str = "blue"
):
    """
    【汎用プロッター】
    プロットデータ、使用した点の情報、ラベル等を受け取り、グラフを描画・保存する。
    Used Dataや近似直線の情報が無い場合は、自動的にそれらを省略して描画する。
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # 1. 全データプロット (背景として薄く表示)
    # マーカー形状は共通で統一 (例えば丸など)
    ax.scatter(x_all, y_all, s=40, c='lightgray', marker='o', edgecolors='gray', label='All Data', zorder=1)
    
    # 軸調整用のデータ範囲（デフォルトは全データ）
    x_for_limits = x_all
    y_for_limits = y_all

    # 2. Used Data & Fit Line (情報がある場合のみ描画)
    if used_indices is not None and len(used_indices) > 0:
        x_valid = x_all[used_indices]
        y_valid = y_all[used_indices]
        
        # Used Dataプロット
        ax.scatter(x_valid, y_valid, s=40, c=color_valid, marker='o', label=data_label_valid, zorder=2)
        
        # 近似直線 (slope/interceptがあり、かつ点が2つ以上ある場合)
        if slope is not None and intercept is not None and len(x_valid) >= 2:
            x_line = np.linspace(np.min(x_valid), np.max(x_valid), 10)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, color='red', lw=2, label='Fit', zorder=3)
        
        # スマートな軸調整は「Used Data」を基準にする
        x_for_limits = x_valid
        y_for_limits = y_valid

    # 3. 軸・タイトル・グリッド設定
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=14)
    ax.grid(True, which='major', linestyle='--', alpha=0.7)
    ax.legend(loc='upper right')

    # 4. 範囲調整 (キリの良いメモリ設定)
    _set_smart_limits(ax, x_for_limits, y_for_limits)

    # 5. 保存処理
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved Plot: {output_path}")


# ---------------------------------------------------------
# 以下、ラッパー関数 (外部から呼び出されるAPI)
# ---------------------------------------------------------

def save_phase_plot(raw_data: RawData, result: AnalysisResult, config, output_dir: str):
    """
    位相プロット用のラッパー
    """
    # 1. データの準備
    x_all = raw_data.df[config.COL_FREQ_SQRT].values
    y_all = raw_data.df[config.COL_PHASE].values
    
    # 2. ラベル・ファイル名の定義
    title = f"alpha = {result.alpha_phase:.2e} m$^2$/s , kd : {result.kd_min:.2f} - {result.kd_max:.2f}"
    save_path = os.path.join(output_dir, "phase_plot.png")

    # 3. 汎用プロッターへ委譲
    _generic_plot_and_save(
        x_all=x_all,
        y_all=y_all,
        output_path=save_path,
        xlabel=r'$\sqrt{f}$ [Hz$^{0.5}$]',
        ylabel=r'Phase [rad]',
        title=title,
        used_indices=result.used_indices,      # 使用した点
        slope=result.slope_phase,              # 近似直線の傾き
        intercept=result.intercept_phase,      # 近似直線の切片
        data_label_valid="Used Data",
        color_valid="orange"
    )

def save_amplitude_plot(raw_data: RawData, result: AnalysisResult, config, output_dir: str):
    """
    振幅プロット用のラッパー
    """
    # 1. データの準備 (振幅は対数変換: ln(Amp * sqrt(f)))
    x_all = raw_data.df[config.COL_FREQ_SQRT].values
    # 【修正】Ampだけでなく、sqrt(f)を掛けてから対数を取る
    y_all = np.log(raw_data.df[config.COL_AMP].values * x_all)
    
    # 2. ラベル・ファイル名の定義
    # ラベルには振幅由来のAlphaを表示
    title = f"alpha = {result.alpha_amp:.2e} m$^2$/s , kd : {result.kd_min:.2f} - {result.kd_max:.2f}"
    save_path = os.path.join(output_dir, "amplitude_plot.png")

    # 3. 汎用プロッターへ委譲
    _generic_plot_and_save(
        x_all=x_all,
        y_all=y_all,
        output_path=save_path,
        xlabel=r'$\sqrt{f}$ [Hz$^{0.5}$]',
        ylabel=r'$\ln(Amplitude \cdot \sqrt{f})$', # 【修正】ラベル変更
        title=title,
        used_indices=result.used_indices,      # 使用した点
        slope=result.slope_amp,                # 近似直線の傾き
        intercept=result.intercept_amp,        # 近似直線の切片
        data_label_valid="Used Data",
        color_valid="blue"
    )