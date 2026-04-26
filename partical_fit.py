import os

from entrypoints.contracts import PlotterRequest
from entrypoints.matplotlib_plotter_entry import run_matplotlib_plotter

def main():
    print("CSVファイルのパスを入力してください。")
    target_input = input(">> ").strip('"\'')
    if not target_input: return
    target_path = os.path.abspath(target_input)
    if not os.path.exists(target_path):
        print(f"Error: File '{target_path}' not found.")
        return

    target_dir = os.path.dirname(target_path)
    target_filename = os.path.basename(target_path)
    response = run_matplotlib_plotter(
        PlotterRequest(
            target_dir=target_dir,
            interactive_fit_csv=target_filename,
        )
    )
    if response.plotted_series_count == 0:
        print("フィット対象データを表示できませんでした。")
    for warning in response.warnings:
        print(f"[Warning] {warning}")

if __name__ == "__main__":
    main()