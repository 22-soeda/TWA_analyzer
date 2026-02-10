import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import sys

# ==========================================
# 定数定義 (Configuration)
# ==========================================
# CSVのカラム名
COL_TIME = 'elapsed_time'  # 経過時間
COL_AMP = 'R_V'            # 振幅
COL_THETA = 'Theta_deg'    # 位相
COL_X = 'Stage_X_um'       # X座標
COL_Y = 'Stage_Y_um'       # Y座標
COL_Z = 'Stage_Z_um'       # Z座標
COL_FREQ = 'Frequency_Hz'  # 周波数

# 単位変換係数 (V -> uV)
AMP_SCALE = 1e6 

# グラフ設定
PLOT_X_LABEL = "Time (s)"
PLOT_Y_LABEL_AMP = "R_V (uV)"
PLOT_Y_LABEL_THETA = "Theta (deg)"

# 出力ファイル接頭辞
PREFIX_AMP = "Amp"
PREFIX_THETA = "Theta"
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

def process_file(filepath, output_dir):
    try:
        # CSV読み込み
        df = pd.read_csv(filepath)
        
        # 必要なカラムの存在確認
        required_cols = [COL_TIME, COL_AMP, COL_THETA, COL_X, COL_Y, COL_Z, COL_FREQ]
        if not all(col in df.columns for col in required_cols):
            print(f"スキップ: {os.path.basename(filepath)} (必要なカラムが不足しています)")
            return

        # === 単位変換 V -> uV ===
        # 元の値を上書きせず、新しい列を作るか、そのまま変換して使用
        # ここでは計算用に一時的にスケールした値を使用します
        amp_scaled = df[COL_AMP] * AMP_SCALE
        
        # 平均値の計算
        mean_x = df[COL_X].mean()
        mean_y = df[COL_Y].mean()
        mean_z = df[COL_Z].mean()
        mean_freq = df[COL_FREQ].mean() * 2  # ルール: 周波数は2倍

        # タイトル文字列の作成 (x, y, z を小数第二位まで表示に変更)
        title_str = f"x = {mean_x:.2f} um, y = {mean_y:.2f} um, z = {mean_z:.2f} um, Freq = {mean_freq:.1f} Hz"

        # 共通のプロット作成関数
        def create_plot(x_data, y_data, y_label, file_prefix):
            plt.figure()
            
            # ルール: 折れ線ではなく点の散布図
            plt.scatter(x_data, y_data, s=10)
            
            # ルール: グリッド線はなくす
            plt.grid(False)
            
            plt.title(title_str)
            plt.xlabel(PLOT_X_LABEL)
            plt.ylabel(y_label)

            # ルール: グラフのデータ範囲の上限と下限は、軸のメモリの値と一致させる
            ax = plt.gca()
            
            # Matplotlibが自動計算した目盛りを取得
            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            
            # データ範囲
            x_min, x_max = x_data.min(), x_data.max()
            y_min, y_max = y_data.min(), y_data.max()
            
            # データを含む目盛りの範囲を計算して設定
            try:
                x_start, x_end = get_enclosing_ticks(xticks, x_min, x_max)
                y_start, y_end = get_enclosing_ticks(yticks, y_min, y_max)
                
                ax.set_xlim(x_start, x_end)
                ax.set_ylim(y_start, y_end)
            except Exception:
                pass # 計算失敗時はデフォルトのまま

            # ファイル名の作成 (例: Amp_z=0.50um.png)
            # 常に小数第二位まで表示するように変更
            z_str = f"{mean_z:.2f}"
            filename = f"{file_prefix}_z={z_str}um.png"
            
            # 保存
            save_path = os.path.join(output_dir, filename)
            plt.savefig(save_path)
            plt.close() # メモリ解放
            print(f"Saved: {filename}")

        # 1. 経過時間 - R_V(振幅) [単位: uV]
        create_plot(df[COL_TIME], amp_scaled, PLOT_Y_LABEL_AMP, PREFIX_AMP)
        
        # 2. 経過時間 - Theta
        create_plot(df[COL_TIME], df[COL_THETA], PLOT_Y_LABEL_THETA, PREFIX_THETA)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    print("=== CSVプロット作成ツール (定数定義版) ===")
    
    # 1. コマンドラインで対話的にファイルを指定
    input_path = input("CSVファイルまたはフォルダのパスを入力してください: ").strip().strip('"').strip("'")
    
    if not os.path.exists(input_path):
        print("指定されたパスが存在しません。")
        return

    # 2. アウトプットするフォルダをコマンドラインで対話的に指定
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

    # 処理対象ファイルのリストアップ
    files_to_process = []
    if os.path.isdir(input_path):
        files_to_process = glob.glob(os.path.join(input_path, "*.csv"))
        print(f"フォルダ '{input_path}' 内のCSVファイルを検索中...")
    elif os.path.isfile(input_path) and input_path.lower().endswith('.csv'):
        files_to_process = [input_path]
    else:
        print("有効なCSVファイルまたはフォルダを指定してください。")
        return

    if not files_to_process:
        print("処理対象のCSVファイルが見つかりませんでした。")
        return

    print(f"{len(files_to_process)} 個のファイルを処理します。")

    # 各ファイルを処理
    for filepath in files_to_process:
        print(f"Processing: {os.path.basename(filepath)}...")
        process_file(filepath, output_dir)

    print("すべての処理が完了しました。")

if __name__ == "__main__":
    main()