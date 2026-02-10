import math

def calculate_details(d, R, a):
    """
    d - (R - sqrt(R^2 - (a/2)^2)) を計算し、
    途中経過の (R - sqrt(R^2 - (a/2)^2)) も一緒に出力する関数
    """
    # 1. 幾何学的なチェック (直径と弦の長さの関係)
    if R < (a / 2):
        print(f"【エラー】半径 R={R} が小さすぎます。弦の半分 a/2={a/2} より大きくしてください。")
        return None, None

    # 2. ルート部分の計算
    term_inside_sqrt = R**2 - (a/2)**2
    sqrt_val = math.sqrt(term_inside_sqrt)

    # 3. 矢高 (sagitta) の計算: (R - sqrt(...)) の部分
    sagitta = R - sqrt_val

    # 4. 最終結果の計算: d - sagitta
    final_result = d - sagitta

    return sagitta, final_result

# --- 値の設定 ---
# エラーが出ないよう、R は a/2 より大きく設定してください
d = 26.5
R = 3.0E3
a = 101.72

# --- 計算実行と表示 ---
sagitta_val, final_val = calculate_details(d, R, a)

if final_val is not None:
    print("-" * 30)
    print(f"入力値: d={d}, R={R}, a={a}")
    print("-" * 30)
    # ご要望の (R - sqrt(...)) の部分
    print(f"矢高 (円弧の高さ) : {sagitta_val:.4f}") 
    # 最終的な計算結果
    print(f"最終結果 (d - 矢高): {final_val:.4f}")
    print("-" * 30)