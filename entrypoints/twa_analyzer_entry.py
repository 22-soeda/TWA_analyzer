import glob
import os
import shutil

from config import AppConfig
from thermal_analysis import file_parser, interactive_ui, visualizer

from .contracts import TwaAnalyzerRequest, TwaAnalyzerResponse


def _perform_save(raw_data, analysis_result, output_root_dir: str) -> bool:
    if analysis_result is None:
        print("  [Skip] 解析結果が無効なため保存をスキップしました。")
        return False

    filename = os.path.basename(raw_data.filepath)
    case_name = os.path.splitext(filename)[0]
    case_dir = os.path.join(output_root_dir, case_name)
    os.makedirs(case_dir, exist_ok=True)
    print(f"  Saving to: {case_dir}")

    analysis_result.save_to_json(case_dir)
    raw_data.save_input_data(case_dir)
    shutil.copy(raw_data.filepath, os.path.join(case_dir, "raw_data.txt"))
    visualizer.save_phase_plot(raw_data, analysis_result, AppConfig, case_dir)
    visualizer.save_amplitude_plot(raw_data, analysis_result, AppConfig, case_dir)
    print("  -> Complete.")
    return True


def run_twa_analyzer(request: TwaAnalyzerRequest) -> TwaAnalyzerResponse:
    target_path = request.input_path
    target_output_dir = request.output_dir
    errors = []
    saved_cases = 0
    skipped_cases = 0

    if not os.path.exists(target_path):
        return TwaAnalyzerResponse(0, 0, 0, [f"パスが見つかりません: {target_path}"])

    if os.path.isfile(target_path):
        files = [target_path]
    else:
        if request.recursive:
            patterns = [
                os.path.join(target_path, "**", "*.txt"),
                os.path.join(target_path, "**", "*.csv"),
            ]
        else:
            patterns = [
                os.path.join(target_path, "*.txt"),
                os.path.join(target_path, "*.csv"),
            ]
        files = sorted(
            {p for pattern in patterns for p in glob.glob(pattern, recursive=request.recursive)}
        )

    os.makedirs(target_output_dir, exist_ok=True)

    print("-" * 50)
    print(f"{len(files)}個のファイルを処理します。")
    print("-" * 50)

    for i, filepath in enumerate(files):
        print(f"\n[{i + 1}/{len(files)}] Processing: {os.path.basename(filepath)}")
        try:
            raw_data = file_parser.load_from_text(filepath)
            plotter = interactive_ui.TWAInteractivePlotter(raw_data, AppConfig)
            if _perform_save(raw_data, plotter.result, target_output_dir):
                saved_cases += 1
            else:
                skipped_cases += 1
        except Exception as e:
            message = f"{filepath}: {e}"
            errors.append(message)
            print(f"[Error] 処理中にエラー: {e}")

    return TwaAnalyzerResponse(
        processed_files=len(files),
        saved_cases=saved_cases,
        skipped_cases=skipped_cases,
        errors=errors,
    )

