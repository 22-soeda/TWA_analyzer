import json
import pandas as pd
import matplotlib.pyplot as plt
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

# 単位変換係数 (V -> uV)
# 前回のプロットと同様に、R_Vとその標準偏差(sigma)をuV単位で表示します
AMP_SCALE = 1e6 

# グラフ設定
PLOT_X_LABEL = "Z Position (um)"
PLOT_Y_LABEL_RV = "R_V (uV)"
PLOT_Y_LABEL_RV_SIGMA = "R_V sigma (uV)"
PLOT_Y_LABEL_THETA = "Theta (deg)"

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
    
    # データ最小値以下の最大の目盛りを探す（なければ最小の目盛り）
    lower = [t for t in ticks if t <= data_min]
    start = lower[-1] if lower else ticks[0]
    
    # データ最大値以上の最小の目盛りを探す（なければ最大の目盛り）
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
                
                # 必要なデータの抽出
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

def create_and_save_plot(df, x_col, y_col, title_str, x_label, y_label, output_path):
    """
    共通のプロット作成・保存関数
    【追加機能】同時にCSVファイルも出力する
    """
    # --- プロット作成処理 ---
    plt.figure()
    
    # ルール: 折れ線ではなく点の散布図
    plt.scatter(df[x_col], df[y_col], s=20, c='blue', alpha=0.7)
    
    # ルール: グリッド線はなくす
    plt.grid(False)
    
    plt.title(title_str)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # ルール: グラフのデータ範囲の上限と下限は、軸のメモリの値と一致させる
    ax = plt.gca()
    
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
        pass # 計算失敗時はデフォルト設定

    # 画像保存
    plt.savefig(output_path)
    plt.close()
    print(f"Saved Image: {os.path.basename(output_path)}")

    # --- CSV出力処理 (追加) ---
    # 出力パスの拡張子を .png から .csv に置換
    csv_output_path = output_path.replace('.png', '.csv')
    
    # プロットに使用したX列とY列のみを抽出して保存
    # index=False にして行番号が含まれないようにする
    try:
        df[[x_col, y_col]].to_csv(csv_output_path, index=False)
        print(f"Saved CSV  : {os.path.basename(csv_output_path)}")
    except Exception as e:
        print(f"CSV保存エラー: {e}")

def main():
    print("=== JSONデータ収集・プロット・CSV出力ツール ===")
    
    # 1. コマンドラインで対話的に入力ディレクトリを指定
    input_path = input("JSONファイルがあるフォルダのパスを入力してください: ").strip().strip('"').strip("'")
    
    if not os.path.exists(input_path) or not os.path.isdir(input_path):
        print("有効なフォルダパスを指定してください。")
        return

    # 2. コマンドラインで対話的に出力ディレクトリを指定
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

    # データ収集
    df = collect_data(input_path)
    
    if df.empty:
        print("処理可能なデータがありませんでした。終了します。")
        return

    # データの前処理 (単位変換とソート)
    # R_V (mean, std) を uV に変換
    df['r_v_mean_uv'] = df['r_v_mean'] * AMP_SCALE
    df['r_v_std_uv'] = df['r_v_std'] * AMP_SCALE
    
    # Z位置でソート (プロットが見やすくなるように)
    df = df.sort_values(by='z')

    # タイトルの作成
    # 全データの周波数平均を計算し、2倍にする
    mean_freq = df['freq_mean'].mean() * 2
    title_str = f"Freq = {mean_freq:.1f} Hz"

    print(f"プロットとCSVを作成中... (タイトル: {title_str})")

    # 3つのグラフを作成 (関数内でCSVも出力されます)
    # 1. Z vs R_V (uV)
    create_and_save_plot(
        df, 'z', 'r_v_mean_uv', 
        title_str, PLOT_X_LABEL, PLOT_Y_LABEL_RV,
        os.path.join(output_dir, OUT_FILENAME_RV)
    )

    # 2. Z vs R_V sigma (uV)
    create_and_save_plot(
        df, 'z', 'r_v_std_uv', 
        title_str, PLOT_X_LABEL, PLOT_Y_LABEL_RV_SIGMA,
        os.path.join(output_dir, OUT_FILENAME_RV_SIGMA)
    )

    # 3. Z vs Theta
    create_and_save_plot(
        df, 'z', 'theta_mean', 
        title_str, PLOT_X_LABEL, PLOT_Y_LABEL_THETA,
        os.path.join(output_dir, OUT_FILENAME_THETA)
    )

    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()