import sys
import os

from entrypoints.contracts import PlotterRequest
from entrypoints.matplotlib_plotter_entry import run_matplotlib_plotter

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
    response = run_matplotlib_plotter(
        PlotterRequest(
            target_dir=target_dir,
            include_errorbars=True,
        )
    )
    if response.plotted_series_count == 0:
        print("表示可能なデータがありませんでした。")
        for warning in response.warnings:
            print(f"[Warning] {warning}")
        return
    for output in response.output_files:
        print(f"保存完了: {output}")
    for label in response.used_labels:
        print(f"ラベル解決: {label}")
    for warning in response.warnings:
        print(f"[Warning] {warning}")

if __name__ == "__main__":
    main()