import pandas as pd
import io
import os

try:
    from .datamodels import RawData # 通常のパッケージとしての実行時
except ImportError:
    from datamodels import RawData # 単体実行時の対策

"""テキストファイルからデータを読み込み、RawDataオブジェクトを生成するモジュール"""
def load_from_text(filepath: str, sep: str = '\t') -> RawData:

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # "sample information" 行を探して区切り位置を特定
    separator_idx = -1
    for i, line in enumerate(lines):
        if "sample information" in line:
            separator_idx = i
            break
    
    # データ部分（DataFrame）のパース
    data_lines = lines[:separator_idx] if separator_idx != -1 else lines
    data_str = "".join(data_lines)
    df = pd.read_csv(io.StringIO(data_str), sep=sep)
    
    # 列名の余分な空白を除去
    df.columns = [c.strip() for c in df.columns]

    # 列名のファイル名部分を削除
    if len(df.columns) > 1:
        common_prefix = os.path.commonprefix(list(df.columns)) # 最長共通接頭辞を取得
        
        if common_prefix and len(common_prefix) < min(len(c) for c in df.columns): # 共通部分があり、かつそれが列名そのものと一致しない（空文字にならない）場合に削除
            new_columns = [] 
            for col in df.columns:
                new_col = col.replace(common_prefix, "", 1) # 先頭の1回だけ置換
                new_columns.append(new_col)
            
            df.columns = new_columns

    # メタデータ部分のパース
    metadata = {}
    if separator_idx != -1:
        meta_lines = lines[separator_idx+1:]
        for line in meta_lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(sep) # タブ区切りで分割

            if len(parts) < 2:
                parts = line.split(None, 1) # 空白区切りで分割

            if len(parts) >= 2: # キーと値が揃っている場合
                key = parts[0].strip()
                val_str = parts[1].strip()
                
                try:
                    val = float(val_str) # 数値に変換を試みる
                    metadata[key] = val
                except ValueError:
                    pass

    return RawData(df=df, metadata=metadata, filepath=filepath)


# ---------------------------------------------------------
# 動作確認用コード (メインブロック)
# ---------------------------------------------------------

if __name__ == "__main__":
    print("==========================================")
    print("   RawData Parser : Interactive Mode")
    print("==========================================")
    print("解析したいテキストファイルのパスを入力してください。")
    print("※ ターミナルにファイルをドラッグ＆ドロップすると簡単に入力できます。")
    print("※ 終了するには 'q' または 'exit' と入力してください。\n")

    while True:
        try:
            # ユーザー入力を待機
            user_input = input("File Path > ").strip()

            # 終了判定
            if user_input.lower() in ["q", "exit", "quit"]:
                print("終了します。")
                break
            
            # 入力が空の場合はスキップ
            if not user_input:
                continue

            # パスのクォート削除 (Windowsなどでパスが " " で囲まれる場合への対策)
            file_path = user_input.strip('"').strip("'")

            # 存在確認
            if not os.path.exists(file_path):
                print(f"[Error] ファイルが見つかりません: {file_path}")
                continue
            
            if not os.path.isfile(file_path):
                print(f"[Error] 指定されたパスはファイルではありません。")
                continue

            # 読み込み実行
            print(f"\nLoading: {file_path} ...")
            result = load_from_text(file_path, sep='\t')

            # --- 結果表示 ---
            print("-" * 50)
            print(f"■ ファイル情報")
            print(f"  Path: {result.filepath}")
            print(f"  Shape: {result.df.shape} (行数, 列数)")
            
            print(f"\n■ データプレビュー (先頭5行)")
            print(result.df.head())
            
            print(f"\n■ 抽出されたメタデータ")
            if result.metadata:
                for k, v in result.metadata.items():
                    print(f"  - {k}: {v}")
            else:
                print("  (メタデータは見つかりませんでした)")
            print("-" * 50)
            print("\n次のファイルを入力してください (または 'q' で終了):")

        except Exception as e:
            print(f"\n[Fatal Error] 処理中にエラーが発生しました:")
            print(f"{e}")
            print("-" * 50)