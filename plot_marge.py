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
MARKER_SIZE = 30            # 散布図の点のサイズ
MARKER_TYPE = 'o'           # 散布図のマーカー形状
FONT_SIZE = 12              # フォントサイズ
OUTPUT_FILENAME = 'plot_output.png' # 出力する画像ファイル名
# ==========================================

def main():
    print("--- CSV重ね描きプロットツール (縦横シフト対応版) ---")
    
    # 1. ディレクトリを対話的に指定
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = input("対象のディレクトリパスを入力してください: ").strip()
        target_dir = target_dir.strip('"').strip("'")

    if not os.path.isdir(target_dir):
        print(f"エラー: ディレクトリ '{target_dir}' が見つかりません。")
        return

    # 2. JSONファイルの探索と読み込み
    json_files = glob.glob(os.path.join(target_dir, "*.json"))
    
    if not json_files:
        print("エラー: 指定されたディレクトリ内にJSONファイル (.json) が見つかりませんでした。")
        return
    
    json_path = json_files[0]
    print(f"設定ファイル: {os.path.basename(json_path)} を読み込みます...")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"エラー: JSONファイルの読み込みに失敗しました。 {e}")
        return

    # JSON形式の判別とデータの取得
    if isinstance(config_data, dict) and "plots" in config_data:
        plot_list = config_data["plots"]
        xlabel_text = config_data.get("xlabel", "X Axis")
        ylabel_text = config_data.get("ylabel", "Y Axis")
    elif isinstance(config_data, list):
        plot_list = config_data
        xlabel_text = "X Axis"
        ylabel_text = "Y Axis"
        print("警告: 旧形式のJSONを検出しました。軸ラベルはデフォルト値を使用します。")
    else:
        print("エラー: JSONファイルの形式が正しくありません。")
        return

    # 3. プロットの準備
    plt.rcParams['font.size'] = FONT_SIZE
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    
    plot_count = 0
    
    # 4. データの読み込みとプロット
    for item in plot_list:
        csv_filename = item.get('csv_file')
        legend_name = item.get('legend', 'No Name')
        shift_z = item.get('shift_z', 0.0) # 横軸シフト量
        shift_y = item.get('shift_y', 0.0) # 縦軸シフト量

        if not csv_filename:
            continue

        csv_path = os.path.join(target_dir, csv_filename)
        
        if not os.path.exists(csv_path):
            print(f"警告: ファイル '{csv_filename}' が見つかりません。スキップします。")
            continue

        try:
            # CSV読み込み (ヘッダー有無に関わらず1,2列目を使用)
            df = pd.read_csv(csv_path)
            
            if df.shape[1] < 2:
                print(f"警告: '{csv_filename}' の列数が不足しています（2列以上必要）。スキップします。")
                continue

            # 1列目をX、2列目をYとして取得
            x_raw = df.iloc[:, 0]
            y_raw = df.iloc[:, 1]
            
            # 数値変換
            x_raw = pd.to_numeric(x_raw, errors='coerce')
            y_raw = pd.to_numeric(y_raw, errors='coerce')
            
            # NaNを除去
            valid_mask = x_raw.notna() & y_raw.notna()
            
            # シフト適用
            x_data = x_raw[valid_mask] + shift_z
            y_data = y_raw[valid_mask] + shift_y

            if len(x_data) == 0:
                print(f"警告: '{csv_filename}' に有効な数値データがありません。")
                continue

            # 散布図プロット
            ax.scatter(x_data, y_data, label=legend_name, s=MARKER_SIZE, marker=MARKER_TYPE)
            
            plot_count += 1
            print(f"プロット追加: {csv_filename} (Label: {legend_name}, Shift X: {shift_z}, Shift Y: {shift_y})")

        except Exception as e:
            print(f"エラー: '{csv_filename}' の処理中にエラーが発生しました: {e}")

    if plot_count == 0:
        print("プロット可能なデータがありませんでした。終了します。")
        return

    # 5. プロット設定の仕上げ
    ax.legend()
    ax.grid(False)
    ax.set_xlabel(xlabel_text)
    ax.set_ylabel(ylabel_text)

    # 軸のメモリ範囲の調整 (Tickに合わせる)
    fig.canvas.draw()
    
    # X軸調整
    xticks = ax.get_xticks()
    if len(xticks) > 1:
        ax.set_xlim(min(xticks), max(xticks))

    # Y軸調整
    yticks = ax.get_yticks()
    if len(yticks) > 1:
        ax.set_ylim(min(yticks), max(yticks))

    # 6. 画像の保存
    output_path = os.path.join(target_dir, OUTPUT_FILENAME)
    try:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n成功: 画像を保存しました -> {output_path}")
    except Exception as e:
        print(f"エラー: 画像の保存に失敗しました: {e}")

if __name__ == "__main__":
    main()