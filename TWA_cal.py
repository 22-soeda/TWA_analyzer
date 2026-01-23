import os
import glob
import shutil
from config import AppConfig
from thermal_analysis import file_parser, interactive_ui, visualizer

def perform_save(raw_data, analysis_result, output_root_dir):
    """保存処理の実体"""
    if analysis_result is None:
        print("  [Skip] 解析結果が無効なため保存をスキップしました。")
        return

    try:
        filename = os.path.basename(raw_data.filepath)
        case_name = os.path.splitext(filename)[0]
        
        case_dir = os.path.join(output_root_dir, case_name)
        os.makedirs(case_dir, exist_ok=True)
        print(f"  Saving to: {case_dir}")

        # JSON保存
        analysis_result.save_to_json(case_dir)
        raw_data.save_input_data(case_dir)
        
        # 生データコピー
        shutil.copy(raw_data.filepath, os.path.join(case_dir, "raw_data.txt"))
        
        # プロット画像生成
        visualizer.save_phase_plot(raw_data, analysis_result, AppConfig, case_dir)
        visualizer.save_amplitude_plot(raw_data, analysis_result, AppConfig, case_dir)
        
        print("  -> Complete.")
        
    except Exception as e:
        print(f"  [Error] 保存処理失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("==========================================")
    print("   TWA Analyzer : Interactive Mode")
    print("==========================================")
    
    # --- Input Path Selection ---
    default_input_dir = AppConfig.INPUT_DIR
    in_input = input(f"Input Path (Default: {default_input_dir}) > ").strip().strip('"').strip("'")
    target_path = in_input if in_input else default_input_dir
    
    if not os.path.exists(target_path):
        print(f"[Error] パスが見つかりません: {target_path}")
        return

    # ファイル検索
    files = []
    if os.path.isfile(target_path):
        files = [target_path]
    elif os.path.isdir(target_path):
        files = glob.glob(os.path.join(target_path, "**", "*.txt"), recursive=True)
    else:
        return

    if not files:
        print("ファイルが見つかりませんでした。")
        return

    # --- Output Path Selection ---
    default_output_dir = AppConfig.OUTPUT_DIR
    out_input = input(f"Output Path (Default: {default_output_dir}) > ").strip().strip('"').strip("'")
    target_output_dir = out_input if out_input else default_output_dir

    if not os.path.exists(target_output_dir):
        os.makedirs(target_output_dir, exist_ok=True)

    print("-" * 50)
    print(f"{len(files)}個のファイルを処理します。")
    print("-" * 50)

    for i, filepath in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Processing: {os.path.basename(filepath)}")
        
        try:
            # 1. ロード
            raw_data = file_parser.load_from_text(filepath)
            
            # 2. UI起動 (ここで範囲選択を行う)
            # ユーザーがウィンドウを閉じるまでブロックします
            plotter = interactive_ui.TWAInteractivePlotter(raw_data, AppConfig)
            
            # 3. UI終了後、plotter.result に格納されている最終結果を保存
            # UIで何も操作しなくても、初期計算結果(全範囲)が入っているため保存されます
            perform_save(raw_data, plotter.result, target_output_dir)
            
        except Exception as e:
            print(f"[Error] 処理中にエラー: {e}")
            continue

    print("-" * 50)
    print("全ての処理が完了しました。")

if __name__ == "__main__":
    main()