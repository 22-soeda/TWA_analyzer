import os
import glob
import json
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ==========================================
# 定数定義 (プロットの基本スタイル)
# ==========================================
FIG_SIZE = (8, 6)           # プロットのサイズ (インチ)
MARKER_SIZE = 6             # マーカーのサイズ
MARKER_TYPE = 'o'           # マーカー形状
CAP_SIZE = 3                # エラーバーの先端の横棒のサイズ
LINE_WIDTH = 1              # エラーバーの線の太さ
FONT_SIZE = 12              # フォントサイズ
OUTPUT_FILENAME = 'plot_output_with_errorbars.png' # 出力ファイル名
# ==========================================

def main():
    print("--- エラーバー付きCSV重ね描きプロットツール ---")
    
    # 1. ディレクトリの指定
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = input("対象のディレクトリパスを入力してください (未入力でカレント): ").strip()
        if not target_dir:
            target_dir = "."
        target_dir = target_dir.strip('"').strip("'")

    if not os.path.isdir(target_dir):
        print(f"エラー: ディレクトリ '{target_dir}' が見つかりません。")
        return

    # 2. JSONファイルの探索と読み込み
    json_files = glob.glob(os.path.join(target_dir, "*.json"))
    if not json_files:
        print("エラー: 指定ディレクトリにJSONファイルが見つかりません。")
        return
    
    config_path = json_files[0]
    print(f"設定ファイルを読み込みます: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"エラー: JSONの読み込みに失敗しました: {e}")
        return

    # 設定の取得
    xlabel_text = config.get("xlabel", "X Axis")
    ylabel_text = config.get("ylabel", "Y Axis")
    headers = config.get("headers", {})
    col_x = headers.get("x")
    col_y = headers.get("y")
    col_y_up = headers.get("y_upper")
    col_y_lo = headers.get("y_lower")
    
    plots_info = config.get("plots", [])

    # 3. プロットの準備
    plt.rcParams.update({'font.size': FONT_SIZE})
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    plot_count = 0
    for p in plots_info:
        csv_filename = p.get("csv_file")
        legend_name = p.get("legend", csv_filename)
        shift_z = p.get("shift_z", 0.0)
        shift_y = p.get("shift_y", 0.0)

        csv_path = os.path.join(target_dir, csv_filename)
        if not os.path.isfile(csv_path):
            print(f"警告: ファイル '{csv_filename}' が見つかりません。スキップします。")
            continue

        try:
            df = pd.read_csv(csv_path)
            
            # 必要なカラムの存在確認
            if col_x not in df.columns or col_y not in df.columns:
                print(f"警告: '{csv_filename}' に指定されたヘッダー {col_x} または {col_y} がありません。")
                continue

            # 数値データの抽出
            df_numeric = df.apply(pd.to_numeric, errors='coerce')
            valid_mask = df_numeric[col_x].notna() & df_numeric[col_y].notna()
            df_valid = df_numeric[valid_mask]

            x_data = df_valid[col_x] + shift_z
            y_data = df_valid[col_y] + shift_y

            # エラーバーの計算 (下限・上限の差分)
            yerr = None
            if col_y_up in df_valid.columns and col_y_lo in df_valid.columns:
                err_lo = y_data - (df_valid[col_y_lo] + shift_y)
                err_up = (df_valid[col_y_up] + shift_y) - y_data
                yerr = [err_lo, err_up]

            # プロット実行
            ax.errorbar(
                x_data, y_data, yerr=yerr, 
                label=legend_name, 
                fmt=MARKER_TYPE, 
                markersize=MARKER_SIZE,
                capsize=CAP_SIZE, 
                elinewidth=LINE_WIDTH,
                linestyle='none' # 線で結ばない場合は 'none'
            )
            
            plot_count += 1
            print(f"プロット追加: {csv_filename}")

        except Exception as e:
            print(f"エラー: '{csv_filename}' の処理中にエラーが発生しました: {e}")

    if plot_count == 0:
        print("表示可能なデータがありませんでした。")
        return

    # 4. 仕上げ
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_xlabel(xlabel_text)
    ax.set_ylabel(ylabel_text)

    plt.tight_layout()
    plt.savefig(os.path.join(target_dir, OUTPUT_FILENAME))
    print(f"保存完了: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    main()