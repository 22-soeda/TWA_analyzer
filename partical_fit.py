import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import matplotlib.ticker as ticker
import numpy as np
import os

# --- 定数定義: グラフの外観設定 ---
FIG_SIZE = (10, 6)          # ウィンドウサイズ (幅, 高さ)
TITLE_FONT_SIZE = 16        # タイトルのフォントサイズ
LABEL_FONT_SIZE = 14        # 軸ラベルのフォントサイズ
TICK_FONT_SIZE = 12         # 軸メモリのフォントサイズ
TEXT_FONT_SIZE = 12         # 近似式のフォントサイズ

# --- 指数表示の設定 ---
DISPLAY_PRECISION = 2       # 表示桁数 (小数点以下の桁数)

# --- 定数定義: データの上限下限設定 ---
X_LIM_MIN = -5
X_LIM_MAX = 4
Y_LIM_MIN = 1.3e-7
Y_LIM_MAX = 0.4e-7

class InteractiveFitter:
    def __init__(self, x, y, xlabel, ylabel, title_prefix, output_dir, output_base_name):
        self.x = np.array(x)
        self.y = np.array(y)
        self.output_dir = output_dir
        self.output_base_name = output_base_name
        
        # プロットの初期化
        self.fig, self.ax = plt.subplots(figsize=FIG_SIZE)
        self.fig.subplots_adjust(top=0.85) # 上部に近似式とタイトル用の余白を確保
        
        # グリッドなし
        self.ax.grid(False)
        
        # タイトルの設定
        self.ax.set_title(title_prefix, fontsize=TITLE_FONT_SIZE, pad=20)
        
        # 散布図 (Scatter)
        self.scat = self.ax.scatter(self.x, self.y, label='Data', color='blue', alpha=0.6)
        
        # 近似に使用したプロットを強調するための散布図
        self.highlight_scat = self.ax.scatter([], [], facecolors='none', edgecolors='red', linewidths=1.5, label='Selected')
        
        # 近似直線
        self.line, = self.ax.plot([], [], 'r-', linewidth=2, label='Fit')
        
        # 近似式のテキスト表示
        self.text = self.ax.text(0.5, 1.02, '', transform=self.ax.transAxes, 
                                 horizontalalignment='center', verticalalignment='bottom',
                                 fontsize=TEXT_FONT_SIZE, color='black')
        
        # 軸ラベルと範囲の設定
        self.ax.set_xlabel(xlabel, fontsize=LABEL_FONT_SIZE)
        self.ax.set_ylabel(ylabel, fontsize=LABEL_FONT_SIZE)
        
        # メモリのフォントサイズと指数表示の設定
        self.ax.tick_params(axis='both', which='major', labelsize=TICK_FONT_SIZE)
        
        # カスタムフォーマッタの適用
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.scientific_formatter))
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(self.scientific_formatter))
        
        if X_LIM_MIN is not None: self.ax.set_xlim(left=X_LIM_MIN)
        if X_LIM_MAX is not None: self.ax.set_xlim(right=X_LIM_MAX)
        if Y_LIM_MIN is not None: self.ax.set_ylim(bottom=Y_LIM_MIN)
        if Y_LIM_MAX is not None: self.ax.set_ylim(top=Y_LIM_MAX)

        self.ax.legend(loc='upper right')

        # 横軸範囲選択のためのセレクター
        self.selector = SpanSelector(
            self.ax, 
            self.onselect, 
            'horizontal', 
            useblit=True,
            props=dict(alpha=0.2, facecolor='red'),
            interactive=True,
            drag_from_anywhere=True
        )

        self.fit_params = None # (slope, intercept)
        self.fig.canvas.mpl_connect('close_event', self.on_close)

    def scientific_formatter(self, val, pos):
        """
        指数表示の条件: 10^-1(0.1) ～ 10^1(10) は通常表示、それ以外は指数表示
        """
        if val == 0:
            return "0"
        abs_v = abs(val)
        if 0.1 <= abs_v <= 10:
            return f"{val:.{DISPLAY_PRECISION}f}"
        else:
            return f"{val:.{DISPLAY_PRECISION}e}"

    def onselect(self, xmin, xmax):
        ind = np.where((self.x >= xmin) & (self.x <= xmax))[0]
        if len(ind) < 2: return 

        x_fit = self.x[ind]
        y_fit = self.y[ind]
        
        # 1次近似
        coef = np.polyfit(x_fit, y_fit, 1)
        slope, intercept = coef
        self.fit_params = coef
        
        poly1d_fn = np.poly1d(coef)
        curr_xlim = self.ax.get_xlim()
        x_line = np.linspace(curr_xlim[0], curr_xlim[1], 100)
        y_line = poly1d_fn(x_line)
        
        self.line.set_data(x_line, y_line)
        self.highlight_scat.set_offsets(np.c_[x_fit, y_fit])
        
        # 式の更新
        eq_text = f'Fit Result: y = {slope:.4f}x + {intercept:.4f}'
        self.text.set_text(eq_text)
        self.fig.canvas.draw_idle()

    def get_output_path(self):
        base, ext = os.path.splitext(self.output_base_name)
        n = 1
        while True:
            filename = f"{base}_fit_{n}.png"
            full_path = os.path.join(self.output_dir, filename)
            if not os.path.exists(full_path):
                return full_path
            n += 1

    def on_close(self, event):
        # 選択範囲（赤い帯）を非表示にする
        self.selector.set_visible(False)
        self.fig.canvas.draw()
        
        save_path = self.get_output_path()
        if self.fit_params is not None:
            print(f"Saving plot with fit result to {save_path}...")
        else:
            print(f"No selection made. Saving original plot to {save_path}...")
        
        self.fig.savefig(save_path, bbox_inches='tight')
        print("Done.")

def load_config(config_path):
    if not os.path.exists(config_path): return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None

def get_plot_settings(config, csv_filename):
    if config is None: return None
    plots = config.get("plots", [])
    for p in plots:
        if p.get("csv_file") == csv_filename: return p
    return None

def main():
    print("CSVファイルのパスを入力してください。")
    target_input = input(">> ").strip('"\'')
    if not target_input: return
    target_path = os.path.abspath(target_input)
    if not os.path.exists(target_path):
        print(f"Error: File '{target_path}' not found.")
        return

    target_dir = os.path.dirname(target_path)
    target_filename = os.path.basename(target_path)
    config_path = os.path.join(target_dir, 'config.json')
    config = load_config(config_path)
    
    if config is None:
        xlabel, ylabel = "X", "Y"
        settings = None
    else:
        xlabel = config.get("xlabel", "X")
        ylabel = config.get("ylabel", "Y")
        settings = get_plot_settings(config, target_filename)

    if settings is None:
        shift_z = 0; shift_y = 0; legend_title = target_filename
    else:
        shift_z = settings.get("shift_z", 0)
        shift_y = settings.get("shift_y", 0)
        legend_title = settings.get("legend", target_filename)

    try:
        df = pd.read_csv(target_path)
        x_data = df.iloc[:, 0].values + shift_z
        y_data = df.iloc[:, 1].values + shift_y
    except Exception as e:
        print(f"Error reading CSV: {e}"); return

    fitter = InteractiveFitter(
        x_data, y_data, xlabel, ylabel, legend_title,
        output_dir=target_dir, output_base_name=target_filename
    )
    plt.show()

if __name__ == "__main__":
    main()