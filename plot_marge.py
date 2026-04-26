import sys
import os

from entrypoints.contracts import PlotterRequest
from entrypoints.matplotlib_plotter_entry import run_matplotlib_plotter

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

    response = run_matplotlib_plotter(
        PlotterRequest(
            target_dir=target_dir,
            include_errorbars=False,
        )
    )
    if response.plotted_series_count == 0:
        print("プロット可能なデータがありませんでした。終了します。")
        for warning in response.warnings:
            print(f"[Warning] {warning}")
        return
    for output in response.output_files:
        print(f"\n成功: 画像を保存しました -> {output}")
    for label in response.used_labels:
        print(f"ラベル解決: {label}")
    for warning in response.warnings:
        print(f"[Warning] {warning}")

if __name__ == "__main__":
    main()