import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import numpy as np
import os
import sys

# --- 定数定義: データの上限下限設定 ---
X_LIM_MIN = -4
X_LIM_MAX = 4
Y_LIM_MIN = -45
Y_LIM_MAX = -5

class InteractiveFitter:
    def __init__(self, x, y, xlabel, ylabel, title_prefix, output_dir, output_base_name):
        self.x = np.array(x)
        self.y = np.array(y)
        self.output_dir = output_dir
        self.output_base_name = output_base_name
        
        # プロットの初期化
        # 上部にテキストを表示するためのスペースを確保するため、topのマージンを調整
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.subplots_adjust(top=0.9) 
        
        # グリッドなし
        self.ax.grid(False)
        
        # 散布図 (Scatter)
        self.scat = self.ax.scatter(self.x, self.y, label='Data', color='blue', alpha=0.6)
        
        # 近似に使用したプロットを強調するための散布図
        self.highlight_scat = self.ax.scatter([], [], facecolors='none', edgecolors='red', linewidths=1.5, label='Selected')
        
        # 近似直線
        self.line, = self.ax.plot([], [], 'r-', linewidth=2, label='Fit')
        
        # 近似式のテキスト表示
        # 変更点: グラフ描画領域の上部外側(y=1.02)に配置することでプロットと重ならないようにする
        self.text = self.ax.text(0.5, 1.02, '', transform=self.ax.transAxes, 
                                 horizontalalignment='center', verticalalignment='bottom',
                                 fontsize=12, color='black')
        
        # 軸ラベルと範囲
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        
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
        """CSVと同じ階層に _fit_n を出力するためのパス生成"""
        base, ext = os.path.splitext(self.output_base_name)
        n = 1
        while True:
            filename = f"{base}_fit_{n}.png"
            full_path = os.path.join(self.output_dir, filename)
            if not os.path.exists(full_path):
                return full_path
            n += 1

    def on_close(self, event):
        if self.fit_params is not None:
            # 画像保存時に選択範囲（赤い帯）を非表示にする
            self.selector.set_visible(False)
            self.fig.canvas.draw()
            
            save_path = self.get_output_path()
            print(f"Saving plot to {save_path}...")
            # bbox_inches='tight' を指定して、枠外のテキストが見切れないように保存
            self.fig.savefig(save_path, bbox_inches='tight')
            print("Done.")
        else:
            print("No fit performed. Nothing saved.")

def load_config(config_path):
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None

def get_plot_settings(config, csv_filename):
    if config is None:
        return None
    plots = config.get("plots", [])
    for p in plots:
        if p.get("csv_file") == csv_filename:
            return p
    return None

def main():
    print("CSVファイルのパスを入力してください。")
    print("ドラッグ&ドロップ入力可 (例: C:/Data/R1.5_amp_ratio.csv)")
    
    target_input = input(">> ").strip('"\'')
    
    if not target_input:
        return

    target_path = os.path.abspath(target_input)
    
    if not os.path.exists(target_path):
        print(f"Error: File '{target_path}' not found.")
        return

    target_dir = os.path.dirname(target_path)
    target_filename = os.path.basename(target_path)

    config_path = os.path.join(target_dir, 'config.json')
    print(f"Looking for config at: {config_path}")
    
    config = load_config(config_path)
    
    if config is None:
        print(f"Warning: 'config.json' not found in {target_dir}")
        print("Proceeding without custom settings (shifts will be 0).")
        xlabel, ylabel = "X", "Y"
        settings = None
    else:
        xlabel = config.get("xlabel", "X")
        ylabel = config.get("ylabel", "Y")
        settings = get_plot_settings(config, target_filename)

    if settings is None:
        if config is not None:
            print(f"Warning: Settings for '{target_filename}' not found inside config.json.")
        shift_z = 0
        shift_y = 0
        legend_title = target_filename
    else:
        shift_z = settings.get("shift_z", 0)
        shift_y = settings.get("shift_y", 0)
        legend_title = settings.get("legend", target_filename)

    try:
        df = pd.read_csv(target_path)
        x_data = df.iloc[:, 0].values + shift_z
        y_data = df.iloc[:, 1].values + shift_y
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"\nProcessing {target_filename}...")
    print(f"Applying Shift -> Z: {shift_z}, Y: {shift_y}")
    
    fitter = InteractiveFitter(
        x_data, 
        y_data, 
        xlabel, 
        ylabel, 
        legend_title,
        output_dir=target_dir,
        output_base_name=target_filename
    )
    
    plt.show()

if __name__ == "__main__":
    main()