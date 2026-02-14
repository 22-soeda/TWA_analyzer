import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# ==========================================
# 0. 解析設定（定数定義）
# ==========================================
FREQ = 64.0        # 測定周波数 [Hz]
IS_DEGREE = True   # True: 度 (Degree), False: ラジアン (Radian)

# 試料・センサー特性
D_SAMPLE = 26.5e-6   # 試料厚み (m)
ALPHA = 1.2e-7       # 試料の熱拡散率 (m^2/s)
E_SAMPLE = 500       # 試料の熱浸透率 (J K^-1 m^-2 s^-1/2)
E_SENSOR = 1340      # センサーの熱浸透率 (J K^-1 m^-2 s^-1/2)
INTERCEPT = np.pi / 4 # 位相補正値 (rad)

# ==========================================
# 1. 入力処理
# ==========================================
def get_csv_path():
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        while True:
            csv_path = input("解析するCSVファイルのパスを入力してください > ").strip()
            csv_path = csv_path.replace('"', '').replace("'", "")
            if os.path.exists(csv_path):
                break
            print(f"エラー: ファイル '{csv_path}' が見つかりません。")
    return os.path.abspath(csv_path)

# ==========================================
# 2. 計算ロジック（関数化）
# ==========================================
def calculate_resistance(theta_rad, freq, d_sample, alpha, e_sample, e_sensor, intercept):
    """
    与えられた位相(rad)とパラメータから熱抵抗Rを計算する
    """
    # 定数計算
    b = e_sensor / e_sample
    sigma = d_sample * np.sqrt(np.pi * freq / alpha)
    sqrt_pi_f = np.sqrt(np.pi * freq)

    # 接触熱抵抗 R の計算
    term_angle = theta_rad + sigma + intercept 
    tan_term = np.tan(term_angle)

    numerator = (1 + b) * tan_term
    denominator = 1 + tan_term
    factor = -1 / (e_sensor * sqrt_pi_f)

    with np.errstate(divide='ignore', invalid='ignore'):
        R_data = factor * (numerator / denominator)
    
    return R_data

# ==========================================
# 3. メイン処理
# ==========================================
def main():
    # パス取得と出力先の設定
    csv_file = get_csv_path()
    output_dir = os.path.dirname(csv_file)
    output_path = os.path.join(output_dir, "Resistance_result.png")

    print(f"-> 対象ファイル: {csv_file}")
    print(f"-> 設定周波数: {FREQ} Hz")

    try:
        df = pd.read_csv(csv_file)
        z_col = df.columns[0]
        theta_col = df.columns[1]
        
        Z_data = df[z_col].values
        Theta_raw = df[theta_col].values

    except Exception as e:
        print(f"エラー: データの読み込みに失敗しました。\n{e}")
        return

    # ---------------------------------------------------------
    # 補正項の総当たり計算と選択
    # ---------------------------------------------------------
    # 試行する補正項 (deg)
    offsets_deg = [0, 360, 180, -180, -360]
    
    results = []

    print("\n" + "="*60)
    print(f"{'No.':<4} {'Offset (deg)':<15} {'Mean R (m^2K/W)':<20} {'Valid Points'}")
    print("-" * 60)

    for i, offset in enumerate(offsets_deg):
        # 位相データの準備 (補正項を加算してからラジアン化)
        if IS_DEGREE:
            # 生データ(deg) + 補正(deg) -> rad
            theta_current_rad = np.deg2rad(Theta_raw + offset)
        else:
            # 生データ(rad) + 補正(deg->rad) -> rad
            theta_current_rad = Theta_raw + np.deg2rad(offset)

        # R計算
        r_vals = calculate_resistance(
            theta_current_rad, FREQ, D_SAMPLE, ALPHA, E_SAMPLE, E_SENSOR, INTERCEPT
        )

        # 平均値の算出 (無限大やNaNを除外)
        valid_r = r_vals[np.isfinite(r_vals)]
        mean_r = np.mean(valid_r) if len(valid_r) > 0 else np.nan
        
        results.append({
            "offset": offset,
            "R_data": r_vals,
            "mean": mean_r
        })

        print(f"{i:<4} {offset:<+15} {mean_r:.4e}           {len(valid_r)}/{len(r_vals)}")

    print("="*60)

    # ユーザー選択
    selected_idx = 0
    while True:
        try:
            choice = input("\n適用する補正項の番号(No.)を入力してください > ").strip()
            idx = int(choice)
            if 0 <= idx < len(offsets_deg):
                selected_idx = idx
                break
            else:
                print(f"0 から {len(offsets_deg)-1} の範囲で入力してください。")
        except ValueError:
            print("有効な数字を入力してください。")

    # 選択されたデータの取得
    selected_offset = results[selected_idx]['offset']
    R_data = results[selected_idx]['R_data']
    print(f"\n-> 選択された補正項: {selected_offset} deg (平均抵抗値: {results[selected_idx]['mean']:.4e})")

    # ---------------------------------------------------------
    # プロット作成
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # --- 上段: 生データ (位相) ---
    # 表示用に補正後の位相もプロットするか、生データのままにするか選択
    # ここでは「生データ」に「選択した補正項」を加えたものを表示します（視覚的確認のため）
    
    if IS_DEGREE:
        plot_theta = Theta_raw + selected_offset
        unit_label = "Degree"
    else:
        plot_theta = Theta_raw + np.deg2rad(selected_offset)
        unit_label = "Radian"

    ax1.scatter(Z_data, plot_theta, color='green', s=10, alpha=0.7, label=f'Phase + {selected_offset} deg')
    ax1.set_xlim(np.min(Z_data), np.max(Z_data))
    
    # Y軸範囲設定 (データ範囲に応じて)
    min_th, max_th = np.min(plot_theta), np.max(plot_theta)
    margin = (max_th - min_th) * 0.1 if max_th != min_th else 1.0
    ax1.set_ylim(min_th - margin, max_th + margin)
    
    ax1.set_ylabel(f"Phase ({unit_label})")
    ax1.set_title(f"Phase Data (f={FREQ}Hz) with Offset {selected_offset} deg")
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend()

    # --- 下段: 計算結果 (接触熱抵抗 R) ---
    ax2.scatter(Z_data, R_data, color='tab:blue', s=15, alpha=0.8, label=f'Calculated R (Offset {selected_offset} deg)')
    ax2.set_xlabel(f"{z_col} (Position)", fontsize=12)
    ax2.set_ylabel(r"Contact Thermal Resistance $R$ ($\mathrm{m^2 K W^{-1}}$)", fontsize=12)
    ax2.set_title("Calculated Contact Thermal Resistance", fontsize=14)
    
    valid_R_plot = R_data[np.isfinite(R_data)]
    if len(valid_R_plot) > 0:
        # 外れ値の影響を避けるため、極端な値を除外してY軸を決める（オプション）
        q1 = np.percentile(valid_R_plot, 5)
        q3 = np.percentile(valid_R_plot, 95)
        rng = q3 - q1
        ax2.set_ylim(q1 - 0.5*rng, q3 + 0.5*rng)
    
    ax2.set_xlim(np.min(Z_data), np.max(Z_data))
    ax2.grid(True, which='both', linestyle=':', alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    
    # 画像の保存
    plt.savefig(output_path, dpi=300)
    print(f"計算完了: グラフを '{output_path}' に保存しました。")
    
    plt.show()

if __name__ == "__main__":
    main()