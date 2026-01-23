import pandas as pd
import io
import os
import numpy as np

try:
    from .datamodels import RawData 
except ImportError:
    from datamodels import RawData 

# configから位相列名を取得するためのインポート
try:
    import config
    PHASE_COL_NAME = config.columns.PHASE
except ImportError:
    PHASE_COL_NAME = "theta" 

def unwrap_phase_custom(phase_data: np.ndarray, period: float = np.pi, threshold: float = 3.0) -> np.ndarray:
    """
    位相アンラップ処理（ベクトル化済み）
    
    隣接点間の差分が threshold (デフォルト3.0) を超えた場合、
    period (デフォルトpi) の整数倍を加減算して連続性を保つように補正します。
    
    Parameters:
      phase_data: 位相データの1次元配列
      period: 補正する周期（ユーザー要件により pi をデフォルト設定）
      threshold: 補正判定を行う差分の閾値（ユーザー要件により 3.0 をデフォルト設定）
                 ※通常のunwrapは period/2 ですが、急激な物理変化を許容するため高めに設定可能です
    """
    # 差分を計算
    diff = np.diff(phase_data)
    
    # 補正が必要な箇所を特定 (閾値を超えた場所)
    # 差分を周期で割って四捨五入することで、補正すべき周期の回数(k)を求める
    # 例: diff=3.2, period=3.14 -> 3.2/3.14=1.01 -> k=1 -> correction = -3.14
    # 例: diff=-3.2 -> k=-1 -> correction = +3.14
    # 閾値以下の変化は k=0 となり補正されない
    
    # 閾値判定マスクを作成
    mask = np.abs(diff) > threshold
    
    # 補正量を計算 (diff / period を四捨五入)
    # mask外の場所は0になるようにする
    k = np.round(diff / period) * mask
    
    correction = -k * period
    
    # 累積和をとって元のデータに加算
    cumulative_correction = np.cumsum(correction)
    
    # 結果配列の作成 (先頭はそのまま、2番目以降に累積補正を足す)
    unwrapped_phase = phase_data.copy()
    unwrapped_phase[1:] += cumulative_correction
    
    return unwrapped_phase

def adjust_phase_continuity(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    DataFrame内の指定列に対して位相アンラップを適用
    """
    if col_name not in df.columns:
        return df
    
    # 値を取得
    phase_values = df[col_name].values
    
    # アンラップ実行 (周期 pi, 閾値 3.0)
    # ※閾値を少し緩めて 0.95 * pi 程度にする案もありますが、
    #   ユーザー様の "pi以上はずれている場合" という直感を尊重して 3.0 (approx 0.95*pi) としています。
    new_phase = unwrap_phase_custom(phase_values, period=np.pi, threshold=3.0)
    
    df[col_name] = new_phase
    return df

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
        common_prefix = os.path.commonprefix(list(df.columns)) 
        
        if common_prefix and len(common_prefix) < min(len(c) for c in df.columns): 
            new_columns = [] 
            for col in df.columns:
                new_col = col.replace(common_prefix, "", 1) 
                new_columns.append(new_col)
            
            df.columns = new_columns

    # --- 位相の補正処理 ---
    if PHASE_COL_NAME in df.columns:
        df = adjust_phase_continuity(df, PHASE_COL_NAME)
    # --------------------

    # メタデータ部分のパース
    metadata = {}
    if separator_idx != -1:
        meta_lines = lines[separator_idx+1:]
        for line in meta_lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(sep) 

            if len(parts) < 2:
                parts = line.split(None, 1) 

            if len(parts) >= 2: 
                key = parts[0].strip()
                val_str = parts[1].strip()
                
                try:
                    val = float(val_str) 
                    metadata[key] = val
                except ValueError:
                    pass

    return RawData(df=df, metadata=metadata, filepath=filepath)


# ---------------------------------------------------------
# 動作確認用コード
# ---------------------------------------------------------

if __name__ == "__main__":
    print("==========================================")
    print("   RawData Parser : Interactive Mode")
    print("==========================================")
    
    # テストデータ生成機能 (動作確認用)
    test_phase = np.array([0.1, 0.2, 3.4, 3.5, 0.3, -3.0]) # 3.4は0.2から+3.2 (wrap), 0.3は3.5から-3.2 (wrap)
    print("Test Phase Raw:", test_phase)
    unwrapped = unwrap_phase_custom(test_phase, period=np.pi, threshold=3.0)
    print("Unwrapped:     ", unwrapped)
    print("-" * 50)

    print("解析したいテキストファイルのパスを入力してください。")
    
    while True:
        try:
            user_input = input("File Path > ").strip()
            if user_input.lower() in ["q", "exit", "quit"]:
                break
            if not user_input:
                continue

            file_path = user_input.strip('"').strip("'")

            if not os.path.exists(file_path):
                print(f"[Error] ファイルが見つかりません: {file_path}")
                continue
            
            print(f"\nLoading: {file_path} ...")
            result = load_from_text(file_path, sep='\t')

            print("-" * 50)
            print(f"■ データプレビュー (先頭5行)")
            print(result.df.head())
            
            if PHASE_COL_NAME in result.df.columns:
                print(f"\n■ 位相データ ({PHASE_COL_NAME}) の一部:")
                print(result.df[PHASE_COL_NAME].values[:10])

        except Exception as e:
            print(f"\n[Error] {e}")