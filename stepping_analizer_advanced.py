import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import sys

# ==========================================
# 定数定義 (Configuration)
# ==========================================
# グラフ設定
PLOT_X_LABEL = "Z Position (um)"
PLOT_Y_LABEL_RATIO = "Ratio (-)"  # 縦軸は無次元量

# ==========================================

def get_enclosing_ticks(ticks, data_min, data_max):
    """
    データ範囲を含む最小と最大の目盛り（tick）を取得する関数
    """
    ticks = sorted(ticks)
    
    # データ最小値以下の最大の目盛りを探す
    lower = [t for t in ticks if t <= data_min]
    start = lower[-1] if lower else ticks[0]
    
    # データ最大値以上の最小の目盛りを探す
    upper = [t for t in ticks if t >= data_max]
    end = upper[0] if upper else ticks[-1]
    
    return start, end

def normalize_column(df, x_col, y_col, n_points):
    """
    X軸(z)でソートし、先頭N点のY平均値の【絶対値】で正規化する
    """
    # データをX軸でソート（CSVがソートされていない場合に備えて）
    df_sorted = df.sort_values(by=x_col).copy()
    
    # リファレンス計算（先頭N点の平均）
    ref_df = df_sorted.head(n_points)
    mean_ref = ref_df[y_col].mean()
    
    # 割る数として絶対値を使用
    abs_mean_ref = abs(mean_ref)
    
    # ログ出力（元の値と絶対値を表示）
    # print(f"  Ref(mean): {mean_ref:.4e}, Ref(abs): {abs_mean_ref:.4e}")

    if abs_mean_ref == 0:
        print(f"  [警告] {y_col} の基準値(絶対値)が0のため正規化できません。")
        df_sorted[y_col + '_ratio'] = df_sorted[y_col]
    else:
        # 絶対値で割ることで、元の符号を維持したまま比率化する
        df_sorted[y_col + '_ratio'] = df_sorted[y_col] / abs_mean_ref
        
    return df_sorted, mean_ref

def create_and_save_plot(df, x_col, y_col, output_png_path, title_base):
    """
    プロット作成・保存およびCSV出力
    """
    # --- プロット作成 ---
    plt.figure()
    
    # 散布図
    plt.scatter(df[x_col], df[y_col], s=20, c='red', alpha=0.7)
    plt.grid(False)
    
    # タイトルとラベル
    plt.title(f"Normalized: {title_base}")
    plt.xlabel(PLOT_X_LABEL)
    plt.ylabel(PLOT_Y_LABEL_RATIO)

    # 軸範囲の調整
    ax = plt.gca()
    try:
        if not df.empty:
            plt.draw() 
            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            
            x_min, x_max = df[x_col].min(), df[x_col].max()
            y_min, y_max = df[y_col].min(), df[y_col].max()
            
            x_start, x_end = get_enclosing_ticks(xticks, x_min, x_max)
            y_start, y_end = get_enclosing_ticks(yticks, y_min, y_max)
            
            ax.set_xlim(x_start, x_end)
            ax.set_ylim(y_start, y_end)
    except Exception:
        pass 

    # 画像保存
    plt.savefig(output_png_path)
    plt.close()
    print(f"  Saved Image: {os.path.basename(output_png_path)}")

    # --- CSV保存 ---
    output_csv_path = output_png_path.replace('.png', '.csv')
    try:
        # 必要な列（ZとRatio）のみ出力
        df[[x_col, y_col]].to_csv(output_csv_path, index=False)
        print(f"  Saved CSV  : {os.path.basename(output_csv_path)}")
    except Exception as e:
        print(f"  CSV保存エラー: {e}")

def get_target_files(input_path):
    """
    入力パスがファイルならそのファイルのみ、
    ディレクトリなら直下のCSV（_ratioを含まない）をリストアップして返す
    """
    target_files = []
    
    if os.path.isfile(input_path):
        if input_path.lower().endswith('.csv'):
            target_files.append(input_path)
        else:
            print("指定されたファイルはCSVではありません。")
            
    elif os.path.isdir(input_path):
        print(f"ディレクトリ内のCSVを検索中...: {input_path}")
        all_csvs = glob.glob(os.path.join(input_path, "*.csv"))
        
        # "_ratio" が含まれないファイルのみ抽出
        for f in all_csvs:
            fname = os.path.basename(f)
            if "_ratio" not in fname:
                target_files.append(f)
                
        print(f"  -> {len(target_files)} 個の未処理CSVファイルが見つかりました。")
        
    else:
        print("指定されたパスが存在しません。")
        
    return sorted(target_files)

def process_single_file(filepath, output_dir, n_points):
    """
    1つのファイルを処理する関数
    """
    filename = os.path.basename(filepath)
    print(f"\nProcessing: {filename}")
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"  エラー: 読み込み失敗 ({e})")
        return

    # カラムの自動判定 ('z' を含むカラムを横軸とみなす)
    x_col = None
    for col in df.columns:
        if 'z' in col.lower():
            x_col = col
            break
    
    if x_col is None:
        print("  エラー: 'z' 列が見つかりません。スキップします。")
        return

    # 横軸以外の全てのカラムを対象に処理
    y_cols = [c for c in df.columns if c != x_col]
    
    if not y_cols:
        print("  エラー: データ列が見つかりません。")
        return

    # 元ファイル名（拡張子なし）
    base_filename = os.path.splitext(filename)[0]

    for y_col in y_cols:
        # 正規化計算 (絶対値で割る)
        df_norm, _ = normalize_column(df, x_col, y_col, n_points)
        
        # 正規化後のカラム名
        y_col_ratio = y_col + '_ratio'
        
        # 出力ファイル名の生成
        if len(y_cols) == 1:
            out_fname = f"{base_filename}_ratio.png"
        else:
            out_fname = f"{base_filename}_{y_col}_ratio.png"
            
        out_path = os.path.join(output_dir, out_fname)
        
        # プロットとCSV保存
        create_and_save_plot(df_norm, x_col, y_col_ratio, out_path, base_filename)

def main():
    print("=== CSV一括正規化・プロットツール (絶対値正規化版) ===")
    
    # 1. 入力パスの指定 (ファイル or ディレクトリ)
    input_path = input("CSVファイル、またはフォルダのパスを入力してください: ").strip().strip('"').strip("'")
    
    target_files = get_target_files(input_path)
    
    if not target_files:
        print("処理対象のCSVファイルがありませんでした。終了します。")
        return

    # 2. 出力ディレクトリの指定
    output_dir = input("出力先フォルダのパスを入力してください: ").strip().strip('"').strip("'")
    
    if not output_dir:
        print("出力先フォルダが指定されていません。")
        return

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"出力フォルダを作成しました: {output_dir}")
        except OSError as e:
            print(f"フォルダ作成失敗: {e}")
            return

    # 3. 正規化点数の指定
    print(f"\n{len(target_files)} 個のファイルを処理します。")
    n_input = input("正規化の基準とするデータ点数 N を入力してください (Zが小さい側): ").strip()
    try:
        n_points = int(n_input)
        if n_points <= 0:
            raise ValueError
    except ValueError:
        print("有効な正の整数が入力されませんでした。処理を中断します。")
        return

    # 一括処理実行
    for filepath in target_files:
        process_single_file(filepath, output_dir, n_points)

    print("\nすべての処理が完了しました。")

if __name__ == "__main__":
    main()