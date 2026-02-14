import os
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ==========================================
# Configuration
# ==========================================
TARGET_AXIS = "z_position"
Y_AXIS_KEY = "thickness_um"
AXIS_LABELS = {
    "x_position": "X Position [um]",
    "y_position": "Y Position [um]",
    "z_position": "Z Position [um]",
    "thickness_um": "Sample Thickness [um]"
}

# グラフ描画設定
PLOT_SETTINGS = {
    "fig_size": (8, 6),      # 画像全体のサイズ (inch)
    "font_size_label": 14,   # 軸ラベルのフォントサイズ
    "font_size_tick": 12,    # 目盛りのフォントサイズ
    "box_aspect": 1.0,       # グラフ枠の縦横比 (高さ/幅)。Noneの場合は指定なし
    "marker_size": 8,        # プロットの点のサイズ
    "show_grid": False       # グリッドの表示有無
}
# ==========================================

def _set_smart_limits(ax, x_data, y_data, margin=0.1):
    """データ範囲に合わせて軸の目盛りを調整する関数"""
    if len(x_data) == 0 or len(y_data) == 0:
        return

    def get_nice_ticks(data_min, data_max, margin_ratio):
        span = data_max - data_min
        if span == 0: span = 1.0
        target_min = data_min - span * margin_ratio
        target_max = data_max + span * margin_ratio
        
        locator = ticker.MaxNLocator(nbins='auto', steps=[1, 2, 2.5, 5, 10])
        ticks = locator.tick_values(target_min, target_max)
        
        if len(ticks) > 1:
            step = ticks[1] - ticks[0]
        else:
            step = span * 0.1 if span > 0 else 0.1
            
        return ticks

    # X軸調整
    x_min, x_max = np.min(x_data), np.max(x_data)
    x_ticks = get_nice_ticks(x_min, x_max, margin)
    if len(x_ticks) >= 2:
        ax.set_xlim(x_ticks[0], x_ticks[-1])
        # ax.set_xticks(x_ticks)

    # Y軸調整
    y_min, y_max = np.min(y_data), np.max(y_data)
    y_ticks = get_nice_ticks(y_min, y_max, margin)
    if len(y_ticks) >= 2:
        ax.set_ylim(y_ticks[0], y_ticks[-1])
        # ax.set_yticks(y_ticks)

def apply_plot_style(ax, xlabel=None, ylabel=None):
    """共通のプロットスタイルを適用する関数"""
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=PLOT_SETTINGS["font_size_label"])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=PLOT_SETTINGS["font_size_label"])
    
    ax.tick_params(axis='both', labelsize=PLOT_SETTINGS["font_size_tick"])
    ax.grid(PLOT_SETTINGS["show_grid"])
    
    if PLOT_SETTINGS["box_aspect"] is not None:
        ax.set_box_aspect(PLOT_SETTINGS["box_aspect"])

def run_summary():
    print("==========================================")
    print("   TWA Analyzer : Thickness Summary Mode")
    print(f"   X Axis : {TARGET_AXIS}")
    print(f"   Y Axis : {Y_AXIS_KEY}")
    print("==========================================")
    
    default_dir = os.path.join(os.getcwd(), "data", "output")
    input_dir = input(f"集計対象の親ディレクトリパスを入力してください (Default: {default_dir}) > ").strip().strip('"').strip("'")
    target_dir = input_dir if input_dir else default_dir
    
    if not os.path.isdir(target_dir):
        print(f"[Error] ディレクトリが見つかりません: {target_dir}")
        return

    print(f"\nSearching for 'results.json' in {target_dir} ...")
    result_files = glob.glob(os.path.join(target_dir, "**", "results.json"), recursive=True)
    
    if not result_files:
        print("results.json が見つかりませんでした。")
        return

    data_list = []
    for fpath in result_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                res = json.load(f)
            
            x_val = res.get(TARGET_AXIS)
            y_val = res.get(Y_AXIS_KEY)
            
            parent_dir_name = os.path.basename(os.path.dirname(fpath))

            if x_val is not None and y_val is not None:
                data_list.append({
                    "id": parent_dir_name,
                    TARGET_AXIS: float(x_val),
                    Y_AXIS_KEY: float(y_val)
                })
        except Exception as e:
            print(f"[Warning] Failed to read {fpath}: {e}")

    if not data_list:
        print(f"有効なデータ（{TARGET_AXIS} および {Y_AXIS_KEY} を含む解析結果）が見つかりませんでした。")
        return

    df = pd.DataFrame(data_list)
    df = df.sort_values(by=TARGET_AXIS)
    
    print(f"集計データ数: {len(df)}")
    print(df[[TARGET_AXIS, Y_AXIS_KEY]].head())

    summary_json_path = os.path.join(target_dir, "summary_thickness.json")
    df.to_json(summary_json_path, orient='records', indent=4)
    print(f"\nSaved Summary JSON: {summary_json_path}")

    # --- プロット作成関数 ---
    def save_plot(x, y, xlabel, ylabel, filename, color):
        if len(x) == 0: return

        fig, ax = plt.subplots(figsize=PLOT_SETTINGS["fig_size"])
        
        # 線なし、マーカーのみ
        ax.plot(x, y, marker='o', linestyle='None', color=color, 
                markersize=PLOT_SETTINGS["marker_size"], label="Measured Thickness")
        
        apply_plot_style(ax, xlabel, ylabel)

        # 軸範囲の自動調整
        _set_smart_limits(ax, x.values, y.values)
        
        save_path = os.path.join(target_dir, filename)
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved Plot: {save_path}")

    save_plot(
        df[TARGET_AXIS], 
        df[Y_AXIS_KEY], 
        xlabel=AXIS_LABELS.get(TARGET_AXIS, TARGET_AXIS),
        ylabel=AXIS_LABELS.get(Y_AXIS_KEY, Y_AXIS_KEY),
        filename="summary_z_vs_thickness.png",
        color="blue"
    )

    print("\n=== 集計完了 ===")

if __name__ == "__main__":
    run_summary()