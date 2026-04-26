from config import AppConfig
from entrypoints.contracts import TwaAnalyzerRequest
from entrypoints.twa_analyzer_entry import run_twa_analyzer

def main():
    print("==========================================")
    print("   TWA Analyzer : Interactive Mode")
    print("==========================================")
    
    # --- Input Path Selection ---
    default_input_dir = AppConfig.INPUT_DIR
    in_input = input(f"Input Path (Default: {default_input_dir}) > ").strip().strip('"').strip("'")
    target_path = in_input if in_input else default_input_dir
    
    # --- Output Path Selection ---
    default_output_dir = AppConfig.OUTPUT_DIR
    out_input = input(f"Output Path (Default: {default_output_dir}) > ").strip().strip('"').strip("'")
    target_output_dir = out_input if out_input else default_output_dir

    request = TwaAnalyzerRequest(
        input_path=target_path,
        output_dir=target_output_dir,
        recursive=True,
    )
    response = run_twa_analyzer(request)

    print("-" * 50)
    print("全ての処理が完了しました。")
    print(
        f"processed={response.processed_files}, saved={response.saved_cases}, "
        f"skipped={response.skipped_cases}, errors={len(response.errors)}"
    )
    for error in response.errors:
        print(f"[Error] {error}")

if __name__ == "__main__":
    main()