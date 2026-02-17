import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import os
import glob
import sys

# ==========================================
# 定数定義 (Configuration)
# ==========================================
# --- グラフ表示設定 ---
# グラフのタイトル (Noneにするとタイトルなし)
PLOT_TITLE = None

# フォントサイズの設定
TITLE_FONT_SIZE = 16    # タイトルのサイズ
LABEL_FONT_SIZE = 16    # 軸ラベル (X, Y) のサイズ
TICK_FONT_SIZE = 16     # メモリ数値および指数表記 (10^n) のサイズ

# プロット（点）のサイズ
MARKER_SIZE = 30

# 指数表記（10^n）を強制する閾値設定
# (0, 0) に設定すると、0以外のすべての数値で指数表記が適用されます
SCIENTIFIC_LIMITS = (-1, 1)

# 軸ラベル
PLOT_X_LABEL = "Z Position (um)"
PLOT_Y_LABEL_RATIO = "Amplitude Ratio (-)"
# --------------------------------------

# ==========================================

def get_enclosing_ticks(ticks, data_min, data_max):
    """
    データ範囲を含む最小と最大の目盛り（tick）を取得する関数
    """
    ticks = sorted(ticks)
    lower = [t for t in ticks if t <= data_min]
    start = lower[-1] if lower else ticks[0]
    upper = [t for t in ticks if t >= data_max]
    end = upper[0] if upper else ticks[-1]
    return start, end

def normalize_column(df, x_col, y_col, n_points):
    """
    X軸(z)でソートし、先頭N点のY平均値の【絶対値】で正規化する
    """
    df_sorted = df.sort_values(by=x_col).copy()
    ref_df = df_sorted.head(n_points)
    mean_ref = ref_df[y_col].mean()
    abs_mean_ref = abs(mean_ref)

    if abs_mean_ref == 0:
        print(f"  [警告] {y_col} の基準値(絶対値)が0のため正規化できません。")
        df_sorted[y_col + '_ratio'] = df_sorted[y_col]
    else:
        df_sorted[y_col + '_ratio'] = df_sorted[y_col] / abs_mean_ref
        
    return df_sorted, mean_ref

def create_and_save_plot(df, x_col, y_col, output_png_path):
    """
    プロット作成・保存およびCSV出力
    """
    plt.figure()
    
    # 散布図 (MARKER_SIZEを適用)
    plt.scatter(df[x_col], df[y_col], s=MARKER_SIZE, c='red', alpha=0.7)
    plt.grid(False)
    
    # タイトルとラベルの設定
    if PLOT_TITLE is not None:
        plt.title(PLOT_TITLE, fontsize=TITLE_FONT_SIZE)
    plt.xlabel(PLOT_X_LABEL, fontsize=LABEL_FONT_SIZE)
    plt.ylabel(PLOT_Y_LABEL_RATIO, fontsize=LABEL_FONT_SIZE)

    ax = plt.gca()
    
    # --- 指数表記（10^n）の設定 ---
    for axis in [ax.xaxis, ax.yaxis]:
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits(SCIENTIFIC_LIMITS)
        axis.set_major_formatter(formatter)
    
    # メモリのフォントサイズを設定
    ax.tick_params(axis='both', which='major', labelsize=TICK_FONT_SIZE)
    ax.xaxis.get_offset_text().set_fontsize(TICK_FONT_SIZE)
    ax.yaxis.get_offset_text().set_fontsize(TICK_FONT_SIZE)

    # 軸範囲の調整
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

    # --- 見切れ防止の処理 ---
    plt.tight_layout()
    plt.savefig(output_png_path, bbox_inches='tight')
    plt.close()
    print(f"  Saved Image: {os.path.basename(output_png_path)}")

    # --- CSV保存 ---
    output_csv_path = output_png_path.replace('.png', '.csv')
    try:
        df[[x_col, y_col]].to_csv(output_csv_path, index=False)
        print(f"  Saved CSV  : {os.path.basename(output_csv_path)}")
    except Exception as e:
        print(f"  CSV保存エラー: {e}")

def get_target_files(input_path):
    """
    対象ファイルのリストアップ
    """
    target_files = []
    if os.path.isfile(input_path):
        if input_path.lower().endswith('.csv'):
            target_files.append(input_path)
    elif os.path.isdir(input_path):
        all_csvs = glob.glob(os.path.join(input_path, "*.csv"))
        for f in all_csvs:
            if "_ratio" not in os.path.basename(f):
                target_files.append(f)
    return sorted(target_files)

def process_single_file(filepath, output_dir, n_points):
    """
    1つのファイルを処理
    """
    filename = os.path.basename(filepath)
    print(f"\nProcessing: {filename}")
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"  エラー: 読み込み失敗 ({e})")
        return

    # 'z' を含むカラムを検索
    x_col = next((col for col in df.columns if 'z' in col.lower()), None)
    if x_col is None:
        print("  エラー: 'z' 列が見つかりません。スキップします。")
        return

    y_cols = [c for c in df.columns if c != x_col]
    base_filename = os.path.splitext(filename)[0]

    for y_col in y_cols:
        df_norm, _ = normalize_column(df, x_col, y_col, n_points)
        y_col_ratio = y_col + '_ratio'
        
        if len(y_cols) == 1:
            out_fname = f"{base_filename}_ratio.png"
        else:
            out_fname = f"{base_filename}_{y_col}_ratio.png"
            
        out_path = os.path.join(output_dir, out_fname)
        create_and_save_plot(df_norm, x_col, y_col_ratio, out_path)

def main():
    print("=== CSV一括正規化・プロットツール (絶対値正規化版) ===")
    
    input_path = input("CSVファイル、またはフォルダのパスを入力してください: ").strip().strip('"').strip("'")
    if not os.path.exists(input_path):
        print("指定されたパスが存在しません。")
        return

    target_files = get_target_files(input_path)
    if not target_files:
        print("処理対象のCSVファイルがありませんでした。終了します。")
        return

    # 出力ディレクトリを入力パスと同じ場所に設定
    if os.path.isfile(input_path):
        output_dir = os.path.dirname(input_path)
    else:
        output_dir = input_path

    print(f"\n{len(target_files)} 個のファイルを処理します。")
    print(f"出力先: {output_dir}")
    
    n_input = input("正規化の基準とするデータ点数 N を入力してください (Zが小さい側): ").strip()
    try:
        n_points = int(n_input)
        if n_points <= 0: raise ValueError
    except ValueError:
        print("有効な正の整数を入力してください。")
        return

    for filepath in target_files:
        process_single_file(filepath, output_dir, n_points)

    print("\nすべての処理が完了しました。")

if __name__ == "__main__":
    main()