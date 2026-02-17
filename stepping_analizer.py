import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import os
import glob
import sys

# ==========================================
# 定数定義 (Configuration)
# ==========================================
# JSON内のキー構造
KEY_Z = 'z_position_um_mean'
KEY_RESULTS = 'results'
KEY_RV = 'R_V'
KEY_THETA = 'Theta_deg'
KEY_FREQ = 'Frequency_Hz'
KEY_MEAN = 'mean'
KEY_STD = 'std'

# --- グラフ表示設定 ---
# グラフのタイトル (Noneにするとタイトルなし)
PLOT_TITLE = None

# フォントサイズの設定
TITLE_FONT_SIZE = 16    # タイトルのサイズ
LABEL_FONT_SIZE = 16    # 軸ラベル (X, Y) のサイズ
TICK_FONT_SIZE = 16     # メモリ数値および指数表記 (10^n) のサイズ

# プロット（点）のサイズ
MARKER_SIZE = 30

# 指数表記（10^n）を強制する閾値設定
# (0, 0) に設定すると、0以外のすべての数値で指数表記が適用されます
SCIENTIFIC_LIMITS = (-1, 2)
# --------------------------------------

# 単位変換係数 (V -> uV)
AMP_SCALE = 1e6 

# グラフ軸ラベル設定
PLOT_X_LABEL = "Z Position (um)"
PLOT_Y_LABEL_RV = "Amplitude (uV)"
PLOT_Y_LABEL_RV_SIGMA = "Amplitude sigma (uV)"
PLOT_Y_LABEL_THETA = "Phase (deg)"

# 出力ファイル名
OUT_FILENAME_RV = "Z_vs_R_V.png"
OUT_FILENAME_RV_SIGMA = "Z_vs_R_V_sigma.png"
OUT_FILENAME_THETA = "Z_vs_Theta.png"
# ==========================================

def get_enclosing_ticks(ticks, data_min, data_max):
    """
    データ範囲を含む最小と最大の目盛り（tick）を取得する関数
    """
    ticks = sorted(ticks)
    lower = [t for t in ticks if t <= data_min]
    start = lower[-1] if lower else ticks[0]
    upper = [t for t in ticks if t >= data_max]
    end = upper[0] if upper else ticks[-1]
    return start, end

def collect_data(input_dir):
    """
    指定ディレクトリ内の全JSONファイルを読み込み、DataFrameを作成する
    """
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    if not json_files:
        print(f"警告: 指定されたディレクトリ '{input_dir}' にJSONファイルが見つかりません。")
        return pd.DataFrame()

    print(f"{len(json_files)} 個のJSONファイルを検出しました。読み込み中...")
    data_list = []
    for filepath in json_files:
        try:
            with open(filepath, 'r') as f:
                d = json.load(f)
                row = {
                    'z': d.get(KEY_Z),
                    'r_v_mean': d[KEY_RESULTS][KEY_RV][KEY_MEAN],
                    'r_v_std': d[KEY_RESULTS][KEY_RV][KEY_STD],
                    'theta_mean': d[KEY_RESULTS][KEY_THETA][KEY_MEAN],
                    'freq_mean': d[KEY_RESULTS][KEY_FREQ][KEY_MEAN]
                }
                data_list.append(row)
        except Exception as e:
            print(f"エラー: {os.path.basename(filepath)} の読み込みに失敗しました ({e})")
            continue
    return pd.DataFrame(data_list)

def create_and_save_plot(df, x_col, y_col, x_label, y_label, output_path):
    """
    共通のプロット作成・保存関数
    """
    plt.figure()
    
    # 散布図の作成
    plt.scatter(df[x_col], df[y_col], s=MARKER_SIZE, c='blue', alpha=0.7)
    plt.grid(False)
    
    # タイトルの設定
    if PLOT_TITLE is not None:
        plt.title(PLOT_TITLE, fontsize=TITLE_FONT_SIZE)
        
    # 軸ラベルの設定
    plt.xlabel(x_label, fontsize=LABEL_FONT_SIZE)
    plt.ylabel(y_label, fontsize=LABEL_FONT_SIZE)

    ax = plt.gca()
    
    # 指数表記（10^n）の設定
    for axis in [ax.xaxis, ax.yaxis]:
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits(SCIENTIFIC_LIMITS)
        axis.set_major_formatter(formatter)
    
    # メモリのフォントサイズを設定
    ax.tick_params(axis='both', which='major', labelsize=TICK_FONT_SIZE)
    
    # 指数（10^n部分）のフォントサイズも設定
    ax.xaxis.get_offset_text().set_fontsize(TICK_FONT_SIZE)
    ax.yaxis.get_offset_text().set_fontsize(TICK_FONT_SIZE)

    # 軸範囲の調整（データがピッタリ収まるように目盛りで制限）
    xticks = ax.get_xticks()
    yticks = ax.get_yticks()
    x_min, x_max = df[x_col].min(), df[x_col].max()
    y_min, y_max = df[y_col].min(), df[y_col].max()
    
    try:
        x_start, x_end = get_enclosing_ticks(xticks, x_min, x_max)
        y_start, y_end = get_enclosing_ticks(yticks, y_min, y_max)
        ax.set_xlim(x_start, x_end)
        ax.set_ylim(y_start, y_end)
    except Exception:
        pass 

    # --- 見切れ防止の処理 ---
    # 1. tight_layout() でラベルが重ならないよう自動調整
    plt.tight_layout()
    
    # 2. savefig の bbox_inches='tight' で画像からはみ出さないように保存
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"Saved Image: {os.path.basename(output_path)}")

    # CSV出力
    csv_output_path = output_path.replace('.png', '.csv')
    try:
        df[[x_col, y_col]].to_csv(csv_output_path, index=False)
        print(f"Saved CSV  : {os.path.basename(csv_output_path)}")
    except Exception as e:
        print(f"CSV保存エラー: {e}")

def main():
    print("=== JSONデータ収集・プロット・CSV出力ツール ===")
    
    input_path = input("JSONファイルがあるフォルダのパスを入力してください: ").strip().strip('"').strip("'")
    if not os.path.exists(input_path) or not os.path.isdir(input_path):
        print("有効なフォルダパスを指定してください。")
        return

    output_dir = input("出力先フォルダのパスを入力してください: ").strip().strip('"').strip("'")
    if not output_dir:
        print("出力先フォルダが指定されていません。")
        return

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"フォルダを作成しました: {output_dir}")
        except OSError as e:
            print(f"フォルダの作成に失敗しました: {e}")
            return

    df = collect_data(input_path)
    if df.empty:
        print("処理可能なデータがありませんでした。終了します。")
        return

    df['r_v_mean_uv'] = df['r_v_mean'] * AMP_SCALE
    df['r_v_std_uv'] = df['r_v_std'] * AMP_SCALE
    df = df.sort_values(by='z')

    print("プロットとCSVを作成中...")
    create_and_save_plot(df, 'z', 'r_v_mean_uv', PLOT_X_LABEL, PLOT_Y_LABEL_RV, os.path.join(output_dir, OUT_FILENAME_RV))
    create_and_save_plot(df, 'z', 'r_v_std_uv', PLOT_X_LABEL, PLOT_Y_LABEL_RV_SIGMA, os.path.join(output_dir, OUT_FILENAME_RV_SIGMA))
    create_and_save_plot(df, 'z', 'theta_mean', PLOT_X_LABEL, PLOT_Y_LABEL_THETA, os.path.join(output_dir, OUT_FILENAME_THETA))

    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()