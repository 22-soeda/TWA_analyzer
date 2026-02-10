import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import os
import glob

# ==========================================
# 設定 (Parameters)
# ==========================================
WINDOW_LENGTH = 11  # 窓枠のサイズ (奇数)
POLY_ORDER = 3      # 近似多項式の次数

# 列名と表示ラベル（単位含む）の対応マップ
# ここに定義された列名は、優先的にこのラベルに変換されます
COLUMN_LABEL_MAP = {
    'z': 'Z / um',
    'theta_mean': 'Theta / deg',
    'r_v_mean_uv': 'R_V / uV',
    'r_v_std_uv': 'R_V sigma / uV',
}
# ==========================================

def get_enclosing_ticks(ticks, data_min, data_max):
    """
    データ範囲をカバーする最小と最大の目盛り（tick）を取得し、
    グラフの枠をメモリ値に一致させるための関数
    """
    ticks = sorted(ticks)
    if not ticks:
        return data_min, data_max
        
    # データ最小値以下の最大の目盛り (なければ最小の目盛り)
    lower = [t for t in ticks if t <= data_min]
    start = lower[-1] if lower else ticks[0]
    
    # データ最大値以上の最小の目盛り (なければ最大の目盛り)
    upper = [t for t in ticks if t >= data_max]
    end = upper[0] if upper else ticks[-1]
    
    return start, end

def clean_label(text):
    """
    列名を簡潔なラベルに変換する
    優先順位:
    1. COLUMN_LABEL_MAP に完全一致するものがあればそれを使う
    2. なければ、汎用ルール（_uv -> / uV など）で変換
    """
    # 1. マップによる直接変換（小文字に統一してチェック）
    if text.lower() in COLUMN_LABEL_MAP:
        return COLUMN_LABEL_MAP[text.lower()]

    # 2. 汎用ルールによる変換
    # 一般的な不要語句を削除
    text_clean = text.replace('_mean', '').replace('_std', '')
    
    # 単位の処理
    units = {
        '_uv': ' / uV',
        '_um': ' / um',
        '_hz': ' / Hz',
        '_deg': ' / deg',
        '_v': ' / V'
    }
    
    unit_str = ""
    for k, v in units.items():
        if text_clean.lower().endswith(k):
            text_clean = text_clean[:-len(k)] # 単位部分を削除
            unit_str = v
            break
            
    # 大文字化などの整形
    parts = text_clean.split('_')
    new_parts = []
    for p in parts:
        if len(p) <= 2: # 短い単語(z, r, vなど)は大文字化
            new_parts.append(p.upper())
        else: # 長い単語(Thetaなど)はCapitalize
            new_parts.append(p.capitalize())
            
    main_label = "_".join(new_parts)
    
    # 単位が見つからなかった場合のデフォルト処理は行わず、そのまま返す
    return f"{main_label}{unit_str}"

def process_file(filepath):
    """
    CSVを読み込み、S-Gフィルタ適用とプロット作成を行う
    """
    filename = os.path.basename(filepath)
    print(f"処理中: {filename} ...")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"エラー: {e}")
        return

    # 列の自動判定 (zを含む列をX、それ以外をY)
    cols = df.columns
    x_col_raw = next((c for c in cols if 'z' in c.lower()), None)
    
    if x_col_raw:
        y_col_raw = next((c for c in cols if c != x_col_raw), None)
    else:
        # zがない場合は1列目をX、2列目をYと仮定
        x_col_raw = cols[0]
        y_col_raw = cols[1] if len(cols) > 1 else None

    if not x_col_raw or not y_col_raw:
        print(f"スキップ: 列の特定に失敗しました - {filename}")
        return

    # ラベルの生成
    x_label = clean_label(x_col_raw)
    y_label = clean_label(y_col_raw)
    
    # タイトル生成 (例: Z vs R_V)
    # 単位(/ uVなど)を除いた部分だけでタイトルを作る
    title_x = x_label.split(' /')[0].strip()
    title_y = y_label.split(' /')[0].strip()
    plot_title = f"{title_x} vs {title_y}"

    # ソートとデータ抽出
    df = df.sort_values(by=x_col_raw)
    x = df[x_col_raw].values
    y = df[y_col_raw].values

    # 窓幅の調整
    current_window = WINDOW_LENGTH
    if len(df) <= WINDOW_LENGTH:
        current_window = len(df) - 1 if (len(df) % 2 == 0) else len(df)
        if current_window < POLY_ORDER + 2:
            print("データ点数不足のためスキップ")
            return
    
    dx = np.mean(np.diff(x))

    try:
        # 計算
        y_smooth = savgol_filter(y, window_length=current_window, polyorder=POLY_ORDER, deriv=0)
        dy_dx = savgol_filter(y, window_length=current_window, polyorder=POLY_ORDER, deriv=1, delta=dx)
    except Exception as e:
        print(f"計算エラー: {e}")
        return

    # --- プロット作成 ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8), sharex=True)
    
    # 上段: 生データとスムージング
    ax1.set_title(plot_title)
    ax1.scatter(x, y, color='blue', alpha=0.5, label='Raw', s=20)
    ax1.plot(x, y_smooth, color='red', linewidth=2, label='Smoothed')
    ax1.set_ylabel(y_label)
    ax1.legend()
    ax1.grid(False) # グリッドなし

    # 下段: 微分
    ax2.plot(x, dy_dx, color='green', linewidth=2, label='Derivative')
    
    # 微分の単位作成 (例: d(R_V) / dZ)
    diff_label = f"d({title_y}) / d({title_x})"
    ax2.set_ylabel(diff_label)
    ax2.set_xlabel(x_label)
    ax2.legend()
    ax2.grid(False)

    # --- 軸範囲の調整 (上下限を目盛りに一致させる) ---
    for ax in [ax1, ax2]:
        # X軸
        xticks = ax.get_xticks()
        x_start, x_end = get_enclosing_ticks(xticks, x.min(), x.max())
        ax.set_xlim(x_start, x_end)
    
    # Y軸 (ax1)
    yticks1 = ax1.get_yticks()
    y1_start, y1_end = get_enclosing_ticks(yticks1, y.min(), y.max())
    ax1.set_ylim(y1_start, y1_end)

    # Y軸 (ax2 - 微分値)
    yticks2 = ax2.get_yticks()
    y2_start, y2_end = get_enclosing_ticks(yticks2, dy_dx.min(), dy_dx.max())
    ax2.set_ylim(y2_start, y2_end)

    plt.tight_layout()
    
    # 保存
    output_filename = os.path.splitext(filepath)[0] + "_analysis.png"
    plt.savefig(output_filename)
    plt.close()
    print(f"保存完了: {os.path.basename(output_filename)}")

def main():
    print("=== S-Gフィルタ解析ツール (単位修正版) ===")
    target_path = input("CSVファイルまたはフォルダのパス: ").strip().strip('"').strip("'")

    if not os.path.exists(target_path):
        print("パスが存在しません。")
        return

    if os.path.isfile(target_path):
        if target_path.lower().endswith('.csv'):
            process_file(target_path)
    elif os.path.isdir(target_path):
        files = glob.glob(os.path.join(target_path, "*.csv"))
        print(f"{len(files)} ファイル検出")
        for f in files:
            process_file(f)
            
    print("完了")

if __name__ == "__main__":
    main()