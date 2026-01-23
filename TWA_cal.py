import os
import glob
import shutil
from config import AppConfig
from thermal_analysis import file_parser, interactive_ui, visualizer

def perform_save(raw_data, analysis_result, output_root_dir):
    """
    保存処理の実体：TWA_cal側で実行
    Caseディレクトリを作成し、結果JSON、入力データJSON、生データコピー、プロット画像を保存する
    """
    if analysis_result is None:
        print("解析結果が存在しないため保存できません。")
        return

    try:
        # 1. ディレクトリ名の決定
        filename = os.path.basename(raw_data.filepath)
        case_name = os.path.splitext(filename)[0]
        
        # 出力先ディレクトリ: {指定されたOutputRoot}/{case_name}
        case_dir = os.path.join(output_root_dir, case_name)
        os.makedirs(case_dir, exist_ok=True)
        print(f"\nSaving to directory: {case_dir} ...")

        # 2. results.json の保存
        analysis_result.save_to_json(case_dir)
        
        # 3. input_data.json の保存
        raw_data.save_input_data(case_dir)
        
        # 4. raw_data.txt (元のテキストファイルのコピー)
        dest_raw_txt = os.path.join(case_dir, "raw_data.txt")
        shutil.copy(raw_data.filepath, dest_raw_txt)
        print(f"Saved Raw Text: {dest_raw_txt}")
        
        # 5. 画像の生成と保存
        # 位相プロット
        visualizer.save_phase_plot(raw_data, analysis_result, AppConfig, case_dir)
        # 振幅プロット
        visualizer.save_amplitude_plot(raw_data, analysis_result, AppConfig, case_dir)
        
        print("=== 全保存完了 ===")
        
    except Exception as e:
        print(f"[Error] 保存処理中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("==========================================")
    print("   TWA Analyzer : Interactive Mode")
    print("==========================================")
    
    # --- Input Path Selection ---
    default_input_dir = AppConfig.INPUT_DIR
    print(f"解析対象のファイルパス、またはディレクトリパスを入力してください。")
    print(f"※ 未入力でEnterを押すと、デフォルトディレクトリ ({default_input_dir}) を探索します。")
    
    in_input = input("Input Path > ").strip()
    in_input = in_input.strip('"').strip("'")
    
    target_path = in_input if in_input else default_input_dir
    
    if not os.path.exists(target_path):
        print(f"[Error] 入力パスが見つかりません: {target_path}")
        return

    # ファイルリストの取得
    files = []
    if os.path.isfile(target_path):
        print(f"Target: Single File -> {target_path}")
        files = [target_path]
    elif os.path.isdir(target_path):
        print(f"Target: Directory -> {target_path}")
        files = glob.glob(os.path.join(target_path, "**", "*.txt"), recursive=True)
    else:
        print("[Error] 指定されたパスはファイルでもディレクトリでもありません。")
        return

    if not files:
        print("解析対象のファイル(.txt)が見つかりませんでした。")
        return

    # --- Output Path Selection ---
    default_output_dir = AppConfig.OUTPUT_DIR
    print(f"\nデータの保存先ディレクトリを入力してください。")
    print(f"※ 未入力でEnterを押すと、デフォルトディレクトリ ({default_output_dir}) に保存します。")

    out_input = input("Output Path > ").strip()
    out_input = out_input.strip('"').strip("'")

    target_output_dir = out_input if out_input else default_output_dir

    # 出力ディレクトリの作成確認
    if not os.path.exists(target_output_dir):
        try:
            os.makedirs(target_output_dir, exist_ok=True)
            print(f"出力ディレクトリを作成しました: {target_output_dir}")
        except Exception as e:
            print(f"[Error] 出力ディレクトリの作成に失敗しました: {e}")
            return

    print("-" * 50)
    print(f"{len(files)}個のファイルが見つかりました。解析を開始します。")
    print("-" * 50)

    # ひとつずつ対話的に処理
    for i, filepath in enumerate(files):
        print(f"[{i+1}/{len(files)}] Opening: {filepath}")
        
        try:
            # 1. ロード
            raw_data = file_parser.load_from_text(filepath)
            
            # 2. 保存用コールバック (ここで指定した target_output_dir を渡す)
            save_callback = lambda r, res: perform_save(r, res, target_output_dir)

            # 3. UI起動
            plotter = interactive_ui.TWAInteractivePlotter(
                raw_data, 
                AppConfig, 
                on_save_callback=save_callback
            )
            
        except Exception as e:
            print(f"[Error] ファイルの処理中にエラーが発生しました: {filepath}")
            print(f"Reason: {e}")
            continue

    print("-" * 50)
    print("全ての処理が完了しました。")

if __name__ == "__main__":
    main()