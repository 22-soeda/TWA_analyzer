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
TARGET_AXIS = "x_position"
AXIS_LABELS = {
    "x_position": "X Position [um]",
    "y_position": "Y Position [um]",
    "z_position": "Z Position [um]"
}
# ==========================================

def _set_smart_limits(ax, x_data, y_data, margin=0.1):
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
        while len(ticks) > 0 and ticks[0] > data_min:
            ticks = np.insert(ticks, 0, ticks[0] - step)
        while len(ticks) > 0 and ticks[-1] < data_max:
            ticks = np.append(ticks, ticks[-1] + step)
        return ticks

    x_min, x_max = np.min(x_data), np.max(x_data)
    x_ticks = get_nice_ticks(x_min, x_max, margin)
    if len(x_ticks) >= 2:
        ax.set_xlim(x_ticks[0], x_ticks[-1])
        ax.set_xticks(x_ticks)

    y_min, y_max = np.min(y_data), np.max(y_data)
    y_ticks = get_nice_ticks(y_min, y_max, margin)
    if len(y_ticks) >= 2:
        ax.set_ylim(y_ticks[0], y_ticks[-1])
        ax.set_yticks(y_ticks)

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
    print(df[[TARGET_AXIS, "alpha_phase", "alpha_ratio"]].head())

    summary_json_path = os.path.join(target_dir, "summary_results.json")
    df.to_json(summary_json_path, orient='records', indent=4)
    print(f"\nSaved Summary JSON: {summary_json_path}")

    # --- プロット作成関数 (タイトル削除) ---
    def save_plot(x, y, ylabel, filename, color):
        if len(x) == 0: return

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y, 'o-', color=color, markersize=8, linewidth=2)
        
        xlabel = AXIS_LABELS.get(TARGET_AXIS, f"{TARGET_AXIS} [um]")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        # ax.set_title(title) <-- 削除
        ax.grid(True, which='major', linestyle='--', alpha=0.7)

        _set_smart_limits(ax, x.values, y.values)
        
        save_path = os.path.join(target_dir, filename)
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved Plot: {save_path}")

    save_plot(
        df[TARGET_AXIS], 
        df["alpha_phase"], 
        ylabel=r"Thermal Diffusivity [m$^2$/s]", 
        filename="summary_pos_alpha.png",
        color="orange"
    )

    save_plot(
        df[TARGET_AXIS], 
        df["alpha_ratio"], 
        ylabel="Alpha Ratio", 
        filename="summary_pos_ratio.png",
        color="green"
    )

    print("\n=== 集計完了 ===")

if __name__ == "__main__":
    run_summary()