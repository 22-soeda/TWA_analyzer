import os
import json
import numpy as np
import pandas as pd
from scipy import stats

# ============================================================
# ユーザー設定セクション (ここを変更して実行してください)
# ============================================================
# 解析対象のフォルダ群が格納されている親ディレクトリのパス
# (Windowsの場合はパスの前に r を付けるか、\\ で区切ってください)
TARGET_PARENT_DIR = r"C:\Users\YourName\Documents\Research\Data"

# 計算に使用する信頼区間 (%)
# 例: 95 -> 95%信頼区間 (両側), 90 -> 90%信頼区間
CONFIDENCE_PERCENT = 95.0
# ============================================================

def create_thermal_diffusivity_summary():
    parent_dir = TARGET_PARENT_DIR
    conf_percent = CONFIDENCE_PERCENT
    
    print(f"解析対象ディレクトリ: {parent_dir}")
    print(f"信頼区間: {conf_percent}%")

    if not os.path.exists(parent_dir):
        print(f"エラー: ディレクトリ '{parent_dir}' が見つかりません。パスを確認してください。")
        return

    # 信頼区間の検証
    if not (0 < conf_percent < 100):
        print("エラー: 信頼区間は 0 より大きく 100 未満の数値を指定してください。")
        return

    summary_list = []

    # 親ディレクトリ内の各アイテムを走査
    print("\n解析を開始します...")
    for item in os.listdir(parent_dir):
        sub_dir = os.path.join(parent_dir, item)
        
        # ディレクトリでない場合はスキップ
        if not os.path.isdir(sub_dir):
            continue
            
        input_path = os.path.join(sub_dir, "input_data.json")
        results_path = os.path.join(sub_dir, "results.json")

        # 必要なファイルが揃っているか確認
        if os.path.exists(input_path) and os.path.exists(results_path):
            try:
                # データの読み込み
                with open(input_path, 'r', encoding='utf-8') as f:
                    input_data = json.load(f)
                with open(results_path, 'r', encoding='utf-8') as f:
                    results_data = json.load(f)

                # パラメータ取得
                z_pos = results_data.get('z_position', None)
                d = results_data.get('thickness_um', 0) * 1e-6  # m単位へ変換
                used_indices = results_data.get('used_indices', [])
                
                # データフレームから抽出
                df_raw = pd.DataFrame(input_data['dataframe']['data'], 
                                     columns=input_data['dataframe']['columns'])
                
                # 指定されたインデックスのデータのみ抽出
                df_used = df_raw.iloc[used_indices]

                x = df_used['sqrt_TW_freq'].values
                y = df_used['theta'].values
                n = len(x)

                if n < 3:
                    print(f"  警告: {item} - データ点数が不足しています (n={n})。")
                    continue

                # 線形回帰 (位相差 theta vs sqrt(f))
                slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
                
                # t値の算出 (指定された信頼区間に基づく)
                # 両側区間なので、(1 + P/100) / 2 の分位点を使用
                # 例: 95% -> 0.975, 90% -> 0.95
                q = 0.5 + (conf_percent / 200.0)
                t_crit = stats.t.ppf(q, n - 2)
                
                delta_b = t_crit * std_err
                
                b_abs = abs(slope)
                b_min = b_abs - delta_b
                b_max = b_abs + delta_b

                # 熱拡散率 alpha = pi * (d / b)^2 の算出
                alpha = np.pi * (d / b_abs)**2
                
                # b_min が正の値であることを確認 (負になると発散するため)
                alpha_upper = np.pi * (d / b_min)**2 if b_min > 0 else float('inf')
                alpha_lower = np.pi * (d / b_max)**2

                # リストに追加
                summary_list.append({
                    "z_position": z_pos,
                    "alpha": alpha,
                    f"alpha_upper_{int(conf_percent)}%": alpha_upper,
                    f"alpha_lower_{int(conf_percent)}%": alpha_lower,
                    "confidence_percent": conf_percent,
                    "slope": slope,
                    "slope_err": std_err,
                    "R2": r_val**2  # 参考用に決定係数も出力
                })
                print(f"  完了: {item} (z={z_pos})")

            except Exception as e:
                print(f"  エラー: {item} の処理中に問題が発生しました: {e}")

    # CSV出力 (指定されたディレクトリ内に保存)
    if summary_list:
        df_summary = pd.DataFrame(summary_list)
        # z_position順にソート
        df_summary = df_summary.sort_values("z_position").reset_index(drop=True)
        
        # 出力パス
        output_filename = "thermal_diffusivity_summary.csv"
        output_path = os.path.join(parent_dir, output_filename)
        df_summary.to_csv(output_path, index=False)
        
        print("-" * 30)
        print(f"解析完了。サマリーを '{output_path}' として保存しました。")
        print(df_summary[["z_position", "alpha", f"alpha_upper_{int(conf_percent)}%", f"alpha_lower_{int(conf_percent)}%"]])
    else:
        print("有効な解析データが見つかりませんでした。")

if __name__ == "__main__":
    create_thermal_diffusivity_summary()