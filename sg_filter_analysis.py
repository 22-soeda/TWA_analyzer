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
WINDOW_LENGTH = 30  # 窓枠のサイズ (奇数)
POLY_ORDER = 3      # 近似多項式の次数

# グラフ描画設定 (全体レイアウト)
PLOT_SETTINGS = {
    "fig_size": (8, 9),      # 画像全体のサイズ
    "font_size_label": 16,   # 軸ラベルのフォントサイズ
    "font_size_tick": 18,    # 目盛りのフォントサイズ
    "font_size_legend": 18,  # 凡例のフォントサイズ
    "box_aspect": 0.6,      # グラフ枠の縦横比
    "show_grid": False,      # グリッドの表示有無
    "hspace": 0.1,           # 上下グラフの隙間
    
    "use_scientific_notation": True,
    "scilimits": (-3, 3),
    "x_tick_step": None,
    "y_tick_step": None
}

# ★ プロットのスタイル設定 (色・サイズなど)
PLOT_STYLE = {
    # 生データ (散布図)
    "raw": {
        "color": "blue",
        "alpha": 0.3,
        "markersize": 6,
        "marker": "o",
        "linestyle": "None"
    },
    # 平滑化データ (折れ線)
    "smoothed": {
        "color": "red",
        "linewidth": 1,
        "linestyle": "-"
    },
    # 微分データ (折れ線)
    "derivative": {
        "color": "green",
        "linewidth": 2,
        "linestyle": "-"
    }
}

# 列名マップ
COLUMN_LABEL_MAP = {
    'z': 'Z Position [um]',
    'theta_mean': 'Phase Difference [deg]',
    'r_v_mean_uv': 'Amplitude [uV]',
    'r_v_std_uv': 'Amplitude Sigma [uV]',
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
    text_clean = text.replace('_mean', '').replace('_std', '')
    units = {'_uv': ' [uV]', '_um': ' [um]', '_hz': ' [Hz]', '_deg': ' [deg]', '_v': ' [V]'}
    unit_str = ""
    for k, v in units.items():
        if text_clean.lower().endswith(k):
            text_clean = text_clean[:-len(k)]
            unit_str = v
            break
    parts = text_clean.split('_')
    new_parts = []
    for p in parts:
        if len(p) <= 2: new_parts.append(p.upper())
        else: new_parts.append(p.capitalize())
    main_label = " ".join(new_parts)
    return f"{main_label}{unit_str}"

def apply_plot_style(ax, xlabel=None, ylabel=None):
    if xlabel: ax.set_xlabel(xlabel, fontsize=PLOT_SETTINGS["font_size_label"])
    if ylabel: ax.set_ylabel(ylabel, fontsize=PLOT_SETTINGS["font_size_label"])
    ax.tick_params(axis='both', labelsize=PLOT_SETTINGS["font_size_tick"])
    ax.grid(PLOT_SETTINGS["show_grid"])
    if PLOT_SETTINGS["box_aspect"] is not None:
        ax.set_box_aspect(PLOT_SETTINGS["box_aspect"])

def _apply_axis_settings(ax, x_data, y_data):
    if len(x_data) == 0 or len(y_data) == 0: return

    x_min, x_max = np.min(x_data), np.max(x_data)
    if PLOT_SETTINGS["x_tick_step"] is not None:
        step = PLOT_SETTINGS["x_tick_step"]
        margin = (x_max - x_min) * 0.1 if x_max != x_min else step
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(step))
    else:
        xticks = ax.get_xticks()
        x_start, x_end = get_enclosing_ticks(xticks, x_min, x_max)
        ax.set_xlim(x_start, x_end)

    y_min, y_max = np.min(y_data), np.max(y_data)
    if PLOT_SETTINGS["y_tick_step"] is not None:
        step = PLOT_SETTINGS["y_tick_step"]
        margin = (y_max - y_min) * 0.1 if y_max != y_min else step
        ax.set_ylim(y_min - margin, y_max + margin)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(step))
    else:
        yticks = ax.get_yticks()
        y_start, y_end = get_enclosing_ticks(yticks, y_min, y_max)
        ax.set_ylim(y_start, y_end)
        
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
    x_col_raw = next((c for c in cols if 'z' in c.lower()), None)
    if x_col_raw:
        y_col_raw = next((c for c in cols if c != x_col_raw), None)
    else:
        x_col_raw = cols[0]
        y_col_raw = cols[1] if len(cols) > 1 else None

    if not x_col_raw or not y_col_raw:
        print(f"スキップ: 列の特定に失敗しました - {filename}")
        return

    x_label = clean_label(x_col_raw)
    y_label = clean_label(y_col_raw)
    title_x = x_label.split(' [')[0].strip()
    title_y = y_label.split(' [')[0].strip()

    df = df.sort_values(by=x_col_raw)
    x = df[x_col_raw].values
    y = df[y_col_raw].values

    current_window = WINDOW_LENGTH
    if len(df) <= WINDOW_LENGTH:
        current_window = len(df) - 1 if (len(df) % 2 == 0) else len(df)
        if current_window < POLY_ORDER + 2:
            print("データ点数不足のためスキップ")
            return
    
    dx = np.mean(np.diff(x))

    try:
        y_smooth = savgol_filter(y, window_length=current_window, polyorder=POLY_ORDER, deriv=0)
        dy_dx = savgol_filter(y, window_length=current_window, polyorder=POLY_ORDER, deriv=1, delta=dx)
    except Exception as e:
        print(f"計算エラー: {e}")
        return

    # --- プロット作成 ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=PLOT_SETTINGS["fig_size"], sharex=True)
    
    # 上段: RawデータとSmoothデータ
    # **PLOT_STYLE["key"] で辞書を展開して引数として渡しています
    ax1.plot(x, y, label='Raw', **PLOT_STYLE["raw"])
    ax1.plot(x, y_smooth, label='Smoothed', **PLOT_STYLE["smoothed"])
    
    ax1.legend(fontsize=PLOT_SETTINGS["font_size_legend"])
    apply_plot_style(ax1, ylabel=y_label)
    _apply_axis_settings(ax1, x, y)

    # 下段: 微分データ
    ax2.plot(x, dy_dx, label='Derivative', **PLOT_STYLE["derivative"])
    
    diff_label = f"d({title_y}) / d({title_x})"
    ax2.legend(fontsize=PLOT_SETTINGS["font_size_legend"])
    apply_plot_style(ax2, xlabel=x_label, ylabel=diff_label)
    _apply_axis_settings(ax2, x, dy_dx)

    # hspace で間隔調整
    plt.subplots_adjust(hspace=PLOT_SETTINGS["hspace"])
    
    output_filename = os.path.splitext(filepath)[0] + "_analysis.png"
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()
    print(f"保存完了: {os.path.basename(output_filename)}")

def main():
    print("=== S-Gフィルタ解析ツール (スタイル設定版) ===")
    target_path = input("CSVファイルまたはフォルダのパス: ").strip().strip('"').strip("'")

    if not os.path.exists(target_path):
        print("パスが存在しません。")
        return

    if os.path.isfile(target_path):
        if target_path.lower().endswith('.csv'):
            process_file(target_path)
    elif os.path.isdir(target_path):
        files = glob.glob(os.path.join(target_path, "*.csv"))
        print(f"{len(files)} ファイル検出")
        for f in files:
            process_file(f)
            
    print("完了")

if __name__ == "__main__":
    main()