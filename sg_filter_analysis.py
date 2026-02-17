import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.signal import savgol_filter
import os
import glob

# ==========================================
# 設定 (Parameters)
# ==========================================
WINDOW_LENGTH = 11  # 窓枠のサイズ (奇数)
POLY_ORDER = 3      # 近似多項式の次数

# グラフ描画設定 (全体レイアウト)
PLOT_SETTINGS = {
    "fig_size": (8, 9),      # 画像全体のサイズ
    "font_size_label": 22,   # 軸ラベルのフォントサイズ
    "font_size_tick": 22,    # 目盛りのフォントサイズ
    "font_size_legend": 22,  # 凡例のフォントサイズ
    "box_aspect": 0.6,      # グラフ枠の縦横比
    "show_grid": False,      # グリッドの表示有無
    "hspace": 0.1,           # 上下グラフの隙間
    
    # --- 表示範囲の設定 (Noneの場合はオートスケール) ---
    "x_lim": (None, None),        # X軸共通範囲 (min, max)
    "y_lim_top": (None, None),    # 上段(Raw/Smooth)のY軸範囲
    "y_lim_bottom": (None, None), # 下段(Derivative)のY軸範囲
    
    "use_scientific_notation": True,
    "scilimits": (-3, 3),
    "x_tick_step": None,
    "y_tick_step": None
}

# ★ プロットのスタイル設定
PLOT_STYLE = {
    "raw": {"color": "blue", "alpha": 0.3, "markersize": 6, "marker": "o", "linestyle": "None"},
    "smoothed": {"color": "red", "linewidth": 1, "linestyle": "-"},
    "derivative": {"color": "green", "linewidth": 2, "linestyle": "-"}
}

# 列名マップ（フル名称）
COLUMN_LABEL_MAP = {
    'z': 'Z Position [um]',
    'theta_mean': 'Phase Difference [deg]',
    'r_v_mean_uv': 'Amplitude [uV]',
    'r_v_std_uv': 'Amplitude Sigma [uV]',
    'r_v_mean_uv_ratio': 'Amplitude Ratio',
}

# ★ 微分表記用の短縮マップ
SHORT_LABEL_MAP = {
    'z': 'z',
    'theta_mean': 'Phase',
    'r_v_mean_uv': 'Amp',
    'r_v_std_uv': 'Amp Sigma',
    'r_v_mean_uv_ratio': 'Amp ratio',
}
# ==========================================

def get_enclosing_ticks(ticks, data_min, data_max):
    ticks = sorted(ticks)
    if not ticks: return data_min, data_max
    lower = [t for t in ticks if t <= data_min]
    start = lower[-1] if lower else ticks[0]
    upper = [t for t in ticks if t >= data_max]
    end = upper[0] if upper else ticks[-1]
    return start, end

def clean_label(text):
    if text.lower() in COLUMN_LABEL_MAP:
        return COLUMN_LABEL_MAP[text.lower()]
    # フォールバック処理
    text_clean = text.replace('_mean', '').replace('_std', '')
    units = {'_uv': ' [uV]', '_um': ' [um]', '_hz': ' [Hz]', '_deg': ' [deg]', '_v': ' [V]'}
    unit_str = ""
    for k, v in units.items():
        if text_clean.lower().endswith(k):
            text_clean = text_clean[:-len(k)]
            unit_str = v
            break
    parts = text_clean.split('_')
    new_parts = [p.upper() if len(p) <= 2 else p.capitalize() for p in parts]
    return f"{" ".join(new_parts)}{unit_str}"

def get_short_label(text):
    """微分表記用の短いラベルを取得"""
    return SHORT_LABEL_MAP.get(text.lower(), text.split('_')[0])

def apply_plot_style(ax, xlabel=None, ylabel=None):
    if xlabel: ax.set_xlabel(xlabel, fontsize=PLOT_SETTINGS["font_size_label"])
    if ylabel: ax.set_ylabel(ylabel, fontsize=PLOT_SETTINGS["font_size_label"])
    ax.tick_params(axis='both', labelsize=PLOT_SETTINGS["font_size_tick"])
    ax.grid(PLOT_SETTINGS["show_grid"])
    if PLOT_SETTINGS["box_aspect"] is not None:
        ax.set_box_aspect(PLOT_SETTINGS["box_aspect"])

def _apply_axis_settings(ax, x_data, y_data, x_lim=(None, None), y_lim=(None, None)):
    if len(x_data) == 0 or len(y_data) == 0: return

    # X軸範囲設定
    x_min_data, x_max_data = np.min(x_data), np.max(x_data)
    final_x_min = x_lim[0] if x_lim[0] is not None else None
    final_x_max = x_lim[1] if x_lim[1] is not None else None

    if PLOT_SETTINGS["x_tick_step"] is not None:
        step = PLOT_SETTINGS["x_tick_step"]
        ax.xaxis.set_major_locator(ticker.MultipleLocator(step))
        if final_x_min is None: final_x_min = x_min_data - (x_max_data - x_min_data) * 0.05
        if final_x_max is None: final_x_max = x_max_data + (x_max_data - x_min_data) * 0.05
    else:
        xticks = ax.get_xticks()
        s, e = get_enclosing_ticks(xticks, x_min_data, x_max_data)
        if final_x_min is None: final_x_min = s
        if final_x_max is None: final_x_max = e
    
    ax.set_xlim(final_x_min, final_x_max)

    # Y軸範囲設定
    y_min_data, y_max_data = np.min(y_data), np.max(y_data)
    final_y_min = y_lim[0] if y_lim[0] is not None else None
    final_y_max = y_lim[1] if y_lim[1] is not None else None

    if PLOT_SETTINGS["y_tick_step"] is not None:
        step = PLOT_SETTINGS["y_tick_step"]
        ax.yaxis.set_major_locator(ticker.MultipleLocator(step))
        if final_y_min is None: final_y_min = y_min_data - (y_max_data - y_min_data) * 0.05
        if final_y_max is None: final_y_max = y_max_data + (y_max_data - y_min_data) * 0.05
    else:
        yticks = ax.get_yticks()
        s, e = get_enclosing_ticks(yticks, y_min_data, y_max_data)
        if final_y_min is None: final_y_min = s
        if final_y_max is None: final_y_max = e
        
    ax.set_ylim(final_y_min, final_y_max)
        
    if PLOT_SETTINGS["use_scientific_notation"]:
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='x', scilimits=PLOT_SETTINGS["scilimits"])
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=PLOT_SETTINGS["scilimits"])

def process_file(filepath):
    filename = os.path.basename(filepath)
    print(f"処理中: {filename} ...")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"エラー: {e}")
        return

    cols = df.columns
    x_col_raw = next((c for c in cols if 'z' in c.lower()), cols[0])
    y_col_raw = next((c for c in cols if c != x_col_raw), cols[1] if len(cols) > 1 else None)

    if not y_col_raw: return

    x_label = clean_label(x_col_raw)
    y_label = clean_label(y_col_raw)
    
    # 短縮ラベルの取得
    short_x = get_short_label(x_col_raw)
    short_y = get_short_label(y_col_raw)

    df = df.sort_values(by=x_col_raw)
    x, y = df[x_col_raw].values, df[y_col_raw].values

    current_window = WINDOW_LENGTH
    if len(df) <= WINDOW_LENGTH:
        current_window = len(df) - 1 if (len(df) % 2 == 0) else len(df)
        if current_window < POLY_ORDER + 2: return
    
    dx = np.mean(np.diff(x))
    y_smooth = savgol_filter(y, window_length=current_window, polyorder=POLY_ORDER, deriv=0)
    dy_dx = savgol_filter(y, window_length=current_window, polyorder=POLY_ORDER, deriv=1, delta=dx)

    # --- プロット作成 ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=PLOT_SETTINGS["fig_size"], sharex=True)
    
    # 上段
    ax1.plot(x, y, label='Raw', **PLOT_STYLE["raw"])
    ax1.plot(x, y_smooth, label='Smoothed', **PLOT_STYLE["smoothed"])
    ax1.legend(fontsize=PLOT_SETTINGS["font_size_legend"])
    apply_plot_style(ax1, ylabel=y_label)
    _apply_axis_settings(ax1, x, y, x_lim=PLOT_SETTINGS["x_lim"], y_lim=PLOT_SETTINGS["y_lim_top"])

    # 下段 (短縮表記を採用)
    ax2.plot(x, dy_dx, label='Derivative', **PLOT_STYLE["derivative"])
    diff_label = f"d({short_y}) / d({short_x})"
    ax2.legend(fontsize=PLOT_SETTINGS["font_size_legend"])
    apply_plot_style(ax2, xlabel=x_label, ylabel=diff_label)
    _apply_axis_settings(ax2, x, dy_dx, x_lim=PLOT_SETTINGS["x_lim"], y_lim=PLOT_SETTINGS["y_lim_bottom"])

    plt.subplots_adjust(hspace=PLOT_SETTINGS["hspace"])
    output_filename = os.path.splitext(filepath)[0] + "_analysis.png"
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()

def main():
    print("=== S-Gフィルタ解析ツール (範囲指定・短縮ラベル版) ===")
    target_path = input("CSVファイルまたはフォルダのパス: ").strip().strip('"').strip("'")
    if not os.path.exists(target_path): return
    
    files = [target_path] if os.path.isfile(target_path) else glob.glob(os.path.join(target_path, "*.csv"))
    for f in files:
        if f.lower().endswith('.csv'): process_file(f)
    print("完了")

if __name__ == "__main__":
    main()