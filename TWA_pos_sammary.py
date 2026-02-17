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
AXIS_LABELS = {
    "x_position": "X Position [um]",
    "y_position": "Y Position [um]",
    "z_position": "Z Position [um]"
}

# グラフ描画設定
PLOT_SETTINGS = {
    "fig_size": (8, 9),      
    "font_size_label": 16,   
    "font_size_tick": 18,    
    "box_aspect": 0.6,       
    "marker_size": 8,        
    "show_grid": False,      
    "hspace": 0.1,           
    
    "use_scientific_notation": True,
    "scilimits": (-3, 3),
    
    "x_tick_step": None,
    "y_tick_step": None
}
# ==========================================

def _apply_axis_settings(ax, x_data, y_data, is_ratio=False):
    if len(x_data) == 0 or len(y_data) == 0:
        return

    # --- 1. X軸の設定 ---
    x_min, x_max = np.min(x_data), np.max(x_data)
    if PLOT_SETTINGS["x_tick_step"] is not None:
        step = PLOT_SETTINGS["x_tick_step"]
        margin = (x_max - x_min) * 0.1 if x_max != x_min else step
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(step))
    else:
        margin = 0.1
        span = x_max - x_min
        if span == 0: span = 1.0
        target_min = x_min - span * margin
        target_max = x_max + span * margin
        locator = ticker.MaxNLocator(nbins='auto', steps=[1, 2, 2.5, 5, 10])
        ticks = locator.tick_values(target_min, target_max)
        if len(ticks) >= 2:
            ax.set_xlim(ticks[0], ticks[-1])
            ax.set_xticks(ticks)

    # --- 2. Y軸の設定 ---
    y_min, y_max = np.min(y_data), np.max(y_data)
    
    current_y_max_limit = None
    if is_ratio:
        if y_max > 1.0:
            current_y_max_limit = 1.0

    if PLOT_SETTINGS["y_tick_step"] is not None:
        step = PLOT_SETTINGS["y_tick_step"]
        margin = (y_max - y_min) * 0.1 if y_max != y_min else step
        lower = y_min - margin
        upper = y_max + margin
        if current_y_max_limit is not None: upper = min(upper, current_y_max_limit)
        elif is_ratio and upper > 1.0: upper = 1.0
        ax.set_ylim(lower, upper)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(step))
    else:
        margin = 0.1
        span = y_max - y_min
        if span == 0: span = 1.0 if not is_ratio else 0.1
        target_min = y_min - span * margin
        target_max = y_max + span * margin
        if current_y_max_limit is not None: target_max = min(target_max, current_y_max_limit)
        elif is_ratio and target_max > 1.0: target_max = 1.0
        locator = ticker.MaxNLocator(nbins='auto', steps=[1, 2, 2.5, 5, 10])
        ticks = locator.tick_values(target_min, target_max)
        if is_ratio: ticks = [t for t in ticks if t <= 1.0000001]
        
        if len(ticks) >= 2:
            ax.set_ylim(ticks[0], ticks[-1])
            ax.set_yticks(ticks)
        elif len(ticks) == 1:
             ax.set_ylim(ticks[0]-span*margin, ticks[0]+span*margin)

    # --- 3. 指数表記の設定 ---
    if PLOT_SETTINGS["use_scientific_notation"]:
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='x', scilimits=PLOT_SETTINGS["scilimits"])
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=PLOT_SETTINGS["scilimits"])

def apply_plot_style(ax, xlabel=None, ylabel=None):
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
    print("   TWA Analyzer : Summary Mode")
    print(f"   Target Axis : {TARGET_AXIS}")
    print("==========================================")
    
    target_dir = input("集計対象の親ディレクトリパスを入力してください > ").strip().strip('"').strip("'")
    
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
            
            pos_val = res.get(TARGET_AXIS)
            alpha_phase = res.get("alpha_phase")
            alpha_ratio = res.get("alpha_ratio")
            filename = os.path.basename(os.path.dirname(fpath))

            if pos_val is not None and alpha_phase is not None:
                data_list.append({
                    "id": filename,
                    TARGET_AXIS: float(pos_val),
                    "alpha_phase": float(alpha_phase),
                    "alpha_ratio": float(alpha_ratio) if alpha_ratio is not None else 0.0
                })
        except Exception as e:
            print(f"[Warning] Failed to read {fpath}: {e}")

    if not data_list:
        print(f"有効なデータ（{TARGET_AXIS}を含む解析結果）が見つかりませんでした。")
        return

    df = pd.DataFrame(data_list)
    df = df.sort_values(by=TARGET_AXIS)
    
    print(f"集計データ数: {len(df)}")
    
    # --- JSONの保存 ---
    summary_json_path = os.path.join(target_dir, "summary_results.json")
    df.to_json(summary_json_path, orient='records', indent=4)
    print(f"\nSaved Summary JSON: {summary_json_path}")

    # --- CSVの保存 (z, thermal diffusivity) ---
    # 必要な列を抽出し、指定のヘッダー名に変更
    csv_df = df[[TARGET_AXIS, "alpha_phase"]].copy()
    csv_df.columns = ["z", "thermal_diffusivity"]
    
    summary_csv_path = os.path.join(target_dir, "summary_results.csv")
    csv_df.to_csv(summary_csv_path, index=False, encoding='utf-8')
    print(f"Saved Summary CSV: {summary_csv_path}")

    # --- プロット作成関数などは変更なし ---
    def save_plot(x, y, ylabel, filename, color, is_ratio=False):
        if len(x) == 0: return
        fig, ax = plt.subplots(figsize=PLOT_SETTINGS["fig_size"])
        ax.plot(x, y, marker='o', linestyle='None', color=color, 
                markersize=PLOT_SETTINGS["marker_size"])
        xlabel = AXIS_LABELS.get(TARGET_AXIS, f"{TARGET_AXIS} [um]")
        apply_plot_style(ax, xlabel, ylabel)
        _apply_axis_settings(ax, x.values, y.values, is_ratio=is_ratio)
        save_path = os.path.join(target_dir, filename)
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved Plot: {save_path}")

    def save_stacked_plot(df, filename):
        if len(df) == 0: return
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=PLOT_SETTINGS["fig_size"], sharex=True)
        ax1.plot(df[TARGET_AXIS], df["alpha_phase"], marker='o', linestyle='None', 
                 markersize=PLOT_SETTINGS["marker_size"], color='orange')
        apply_plot_style(ax1, ylabel=r"Thermal Diffusivity [m$^2$/s]")
        _apply_axis_settings(ax1, df[TARGET_AXIS].values, df["alpha_phase"].values, is_ratio=False)
        ax2.plot(df[TARGET_AXIS], df["alpha_ratio"], marker='o', linestyle='None', 
                 markersize=PLOT_SETTINGS["marker_size"], color='green')
        xlabel = AXIS_LABELS.get(TARGET_AXIS, f"{TARGET_AXIS} [um]")
        apply_plot_style(ax2, xlabel=xlabel, ylabel="Alpha Ratio")
        _apply_axis_settings(ax2, df[TARGET_AXIS].values, df["alpha_ratio"].values, is_ratio=True)
        plt.subplots_adjust(hspace=PLOT_SETTINGS["hspace"])
        save_path = os.path.join(target_dir, filename)
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved Stacked Plot: {save_path}")

    save_plot(df[TARGET_AXIS], df["alpha_phase"], ylabel=r"Thermal Diffusivity [m$^2$/s]", 
              filename="summary_pos_alpha.png", color="orange", is_ratio=False)
    save_plot(df[TARGET_AXIS], df["alpha_ratio"], ylabel="Alpha Ratio", 
              filename="summary_pos_ratio.png", color="green", is_ratio=True)
    save_stacked_plot(df, "summary_pos_stacked.png")

    print("\n=== 集計完了 ===")

if __name__ == "__main__":
    run_summary()