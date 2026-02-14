import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import sys

# ==========================================
# 1. 設定 (Parameters)
# ==========================================
# 近似多項式の次数
DEGREE = 10

# プロットの密度 (元データの何倍の細かさで曲線を描くか)
DENSITY_FACTOR = 10

# グラフ描画設定 (全体レイアウト・フォント)
PLOT_SETTINGS = {
    "fig_size": (10, 10),    # 画像全体のサイズ (縦長に変更)
    "font_size_label": 14,   # 軸ラベルのフォントサイズ
    "font_size_tick": 12,    # 目盛りのフォントサイズ
    "font_size_legend": 12,  # 凡例のフォントサイズ
    "hspace": 0.15,          # 上下グラフの隙間
}

# プロットのスタイル (色・マーカーなど)
PLOT_STYLE = {
    # 元データ (散布図)
    "raw": {
        "color": "blue",
        "alpha": 0.5,
        "markersize": 5,
        "marker": "o",
        "linestyle": "None",
        "label": "Original Data"
    },
    # 近似曲線 (実線)
    "fit": {
        "color": "red",
        "linewidth": 2,
        "linestyle": "-",
        "label": f"Poly Fit (deg={DEGREE})"
    },
    # 微分曲線 (実線)
    "derivative": {
        "color": "green",
        "linewidth": 2,
        "linestyle": "-",
        "label": "Derivative"
    }
}
# ==========================================

def adjust_axis_limits_to_ticks(ax, x_data, y_data):
    """
    軸の上限下限を、表示されている目盛りの端に一致させる関数
    """
    # データをすべて表示できるようにレイアウト調整
    # まず自動設定させる
    ax.relim()
    ax.autoscale_view()
    
    # 現在のティックを取得
    xticks = ax.get_xticks()
    yticks = ax.get_yticks()
    
    # ティックの間隔を取得
    if len(xticks) > 1:
        step_x = xticks[1] - xticks[0]
        # データがはみ出している場合、ティックを外側に拡張
        if xticks[0] > np.min(x_data):
            xticks = np.insert(xticks, 0, xticks[0] - step_x)
        if xticks[-1] < np.max(x_data):
            xticks = np.append(xticks, xticks[-1] + step_x)
            
    if len(yticks) > 1:
        step_y = yticks[1] - yticks[0]
        if yticks[0] > np.min(y_data):
            yticks = np.insert(yticks, 0, yticks[0] - step_y)
        if yticks[-1] < np.max(y_data):
            yticks = np.append(yticks, yticks[-1] + step_y)

    # 軸のリミットをティックの端に設定
    ax.set_xlim(xticks[0], xticks[-1])
    ax.set_ylim(yticks[0], yticks[-1])
    
    # ティックを再設定して固定
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    
    # フォントサイズ適用
    ax.tick_params(axis='both', labelsize=PLOT_SETTINGS["font_size_tick"])

def main():
    print("=== 多項式近似解析ツール (微分プロット付き) ===")
    
    # ---------------------------------------------------------
    # 2. ファイル入力
    # ---------------------------------------------------------
    input_path = input("CSVファイルのパスを入力してください: ").strip().strip('"').strip("'")

    if not os.path.exists(input_path):
        print(f"エラー: ファイル '{input_path}' が見つかりません。")
        return

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"エラー: ファイル読み込み失敗\n{e}")
        return

    if df.shape[1] < 2:
        print("エラー: データには少なくとも2列が必要です。")
        return
        
    x_col = df.columns[0]
    y_col = df.columns[1]
    
    # データをソート（X軸が順番通りでないとグラフが乱れるため）
    df = df.sort_values(by=x_col)
    x = df[x_col].values
    y = df[y_col].values

    # ---------------------------------------------------------
    # 3. 近似計算と微分
    # ---------------------------------------------------------
    # 多項式近似 (y = f(x))
    coefficients = np.polyfit(x, y, DEGREE)
    poly_func = np.poly1d(coefficients)
    
    # 微分 (dy/dx = f'(x))
    poly_deriv_func = np.polyder(poly_func)

    # 式の出力
    print("\n" + "=" * 50)
    print(f"近似多項式 (次数: {DEGREE})")
    print("-" * 50)
    print(poly_func)
    print("\n" + "-" * 50)
    print("導関数 (微分)")
    print("-" * 50)
    print(poly_deriv_func)
    print("=" * 50 + "\n")

    # プロット用高密度データ生成
    x_dense = np.linspace(x.min(), x.max(), len(x) * DENSITY_FACTOR)
    y_dense = poly_func(x_dense)
    y_deriv_dense = poly_deriv_func(x_dense)

    # ---------------------------------------------------------
    # 4. プロット作成 (上下2段)
    # ---------------------------------------------------------
    # sharex=TrueでX軸を共有
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=PLOT_SETTINGS["fig_size"], sharex=True)

    # --- 上段: 元データと近似曲線 ---
    ax1.plot(x, y, **PLOT_STYLE["raw"])
    ax1.plot(x_dense, y_dense, **PLOT_STYLE["fit"])
    
    ax1.set_ylabel(y_col, fontsize=PLOT_SETTINGS["font_size_label"])
    ax1.legend(fontsize=PLOT_SETTINGS["font_size_legend"], loc='best')
    ax1.grid(False)

    # --- 下段: 微分曲線 ---
    ax2.plot(x_dense, y_deriv_dense, **PLOT_STYLE["derivative"])
    
    # Y軸ラベル: d(y_col)/d(x_col) のような表記を作成
    deriv_label = f"d({y_col}) / d({x_col})"
    ax2.set_ylabel(deriv_label, fontsize=PLOT_SETTINGS["font_size_label"])
    ax2.set_xlabel(x_col, fontsize=PLOT_SETTINGS["font_size_label"])
    ax2.legend(fontsize=PLOT_SETTINGS["font_size_legend"], loc='best')
    ax2.grid(False)

    # グラフ間の隙間調整
    plt.subplots_adjust(hspace=PLOT_SETTINGS["hspace"])

    # ---------------------------------------------------------
    # 5. 軸設定の調整 (メモリと端の一致)
    # ---------------------------------------------------------
    # レイアウトを確定させてから軸を調整
    # Matplotlibの自動計算を走らせる
    fig.canvas.draw() 

    # 上段の軸調整
    adjust_axis_limits_to_ticks(ax1, x, y)
    
    # 下段の軸調整
    # (X軸は共有されているため、adjust_axis_limits_to_ticksを呼ぶと上書きされるが、
    #  x_denseの範囲はxと同じなので問題ない。y軸のみ個別に調整が必要)
    adjust_axis_limits_to_ticks(ax2, x_dense, y_deriv_dense)

    # sharexの影響でX軸のティックが変わる可能性があるため、最後にX軸範囲を再確認して同期
    # (下段のX軸を基準に統一)
    ax1.set_xlim(ax2.get_xlim())
    ax1.set_xticks(ax2.get_xticks())

    # ---------------------------------------------------------
    # 6. 保存
    # ---------------------------------------------------------
    dir_name = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{base_name}_poly_fit_deriv.png"
    
    # 入力ファイルと同じディレクトリがない場合(カレントディレクトリの場合など)の処理
    if dir_name:
        output_path = os.path.join(dir_name, output_filename)
    else:
        output_path = output_filename
    
    plt.savefig(output_path, bbox_inches='tight')
    print(f"プロットを保存しました: {output_path}")
    
    plt.show()

if __name__ == "__main__":
    main()