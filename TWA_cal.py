import os
import glob
from config import AppConfig
from thermal_analysis import file_parser, interactive_ui

def main():
    # データディレクトリの設定
    target_dir = "./data_raw"
    files = glob.glob(os.path.join(target_dir, "*.txt"))
    
    if not files:
        print("解析対象のファイルが見つかりません。./data_raw にデータを置いてください。")
        # テスト用ダミー生成機能などを入れても良い
        return

    print(f"{len(files)}個のファイルが見つかりました。")

    # ひとつずつ対話的に処理
    for filepath in files:
        print(f"Opening: {filepath}")
        
        # 1. ロード
        raw_data = file_parser.load_from_text(filepath)
        
        # 2. UI起動 (ここでブロッキングされ、閉じると次へ進む)
        # 実際には「次へ」ボタンなどをUIにつけるか、
        # あるいは1ファイル終わるごとにウィンドウを閉じる運用になります。
        plotter = interactive_ui.TWAInteractivePlotter(raw_data, AppConfig)

if __name__ == "__main__":
    main()