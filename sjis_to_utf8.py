import os
import sys

# 変換対象とする拡張子のリスト (必要に応じて追加・変更してください)
TARGET_EXTENSIONS = {'.txt', '.csv', '.log', '.dat', '.xml', '.json', '.py', '.md'}

def is_target_file(filename):
    """拡張子に基づいて変換対象か判定する"""
    _, ext = os.path.splitext(filename)
    return ext.lower() in TARGET_EXTENSIONS

def convert_file(filepath):
    """ファイルをShift-JIS(CP932)からUTF-8に変換して上書き保存する"""
    
    # 1. 既にUTF-8かチェック (二重変換防止)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read()
        print(f"[スキップ] 既にUTF-8です: {filepath}")
        return
    except UnicodeDecodeError:
        pass # UTF-8ではないので次へ
    except Exception as e:
        print(f"[エラー] 読み込み失敗: {filepath} - {e}")
        return

    # 2. Shift-JIS (CP932) で読み込み
    content = ""
    try:
        # cp932はshift_jisの拡張で、Windowsの特殊文字に対応しています
        with open(filepath, 'r', encoding='cp932') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"[スキップ] Shift-JIS(CP932)で読み込めませんでした (バイナリ等の可能性): {filepath}")
        return
    except Exception as e:
        print(f"[エラー] {filepath} - {e}")
        return

    # 3. UTF-8 で書き込み (上書き)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[変換完了] {filepath}")
    except Exception as e:
        print(f"[エラー] 書き込み失敗: {filepath} - {e}")

def main():
    print("Shift-JIS (CP932) のファイルを UTF-8 に変換します。")
    print("--------------------------------------------------")
    
    # パスの入力（引用符が含まれていても除去します）
    input_path = input("ファイルまたはディレクトリのパスを入力してください: ").strip().strip('"').strip("'")

    if not os.path.exists(input_path):
        print("エラー: 指定されたパスが見つかりません。")
        return

    if os.path.isfile(input_path):
        # 単一ファイルの場合
        convert_file(input_path)
        
    elif os.path.isdir(input_path):
        # ディレクトリの場合
        print(f"ディレクトリ内の対象ファイル ({', '.join(TARGET_EXTENSIONS)}) を変換します...")
        files = os.listdir(input_path)
        count = 0
        for filename in files:
            full_path = os.path.join(input_path, filename)
            
            # ディレクトリはスキップし、指定した拡張子のファイルのみ処理
            if os.path.isfile(full_path) and is_target_file(filename):
                convert_file(full_path)
                count += 1
        
        if count == 0:
            print("変換対象の拡張子を持つファイルが見つかりませんでした。")
    
    print("\n処理が終了しました。")

if __name__ == "__main__":
    main()