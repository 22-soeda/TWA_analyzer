import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
import matplotlib.ticker as ticker
import numpy as np
from .datamodels import RawData, AnalysisResult
from . import analyzer  # 新しいモジュールを使用

class TWAInteractivePlotter:
    def __init__(self, raw_data: RawData, config):
        self.raw = raw_data
        self.config = config
        
        # 最終的な解析結果を保持する変数
        self.result: AnalysisResult = None

        # --- データ準備 ---
        self.x_data = raw_data.df[config.COL_FREQ_SQRT].values
        self.phase_data = raw_data.df[config.COL_PHASE].values
        
        # --- 状態管理 ---
        self.n_points = len(self.x_data)
        self.manual_mask = np.ones(self.n_points, dtype=bool) 
        self.range_mask = np.ones(self.n_points, dtype=bool) 
        
        # --- プロット初期化 ---
        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        plt.subplots_adjust(bottom=0.2) 

        self.setup_plot()
        
        # --- インタラクション ---
        self.span = SpanSelector(
            self.ax, self.on_range_select, 'horizontal', useblit=True,
            props=dict(alpha=0.1, facecolor='green'),
            interactive=True, drag_from_anywhere=True
        )
        self.fig.canvas.mpl_connect('pick_event', self.on_point_pick)
        
        # --- ボタン ---
        # "Save"ボタンは削除し、"Complete"のみにする（保存はメインスクリプトの責務）
        ax_comp = plt.axes([0.8, 0.05, 0.1, 0.075])
        self.btn_comp = Button(ax_comp, 'Complete')
        self.btn_comp.on_clicked(self.on_complete)

        # 初回計算 & 軸調整
        self.update_plot_and_calc()
        self.set_global_limits()
        
        plt.show()

    def setup_plot(self):
        self.ax.set_xlabel(r'$\sqrt{f}$ [Hz$^{0.5}$]')
        self.ax.set_ylabel(r'Phase [rad]', color='black')
        self.ax.grid(True, which='major', linestyle='--', alpha=0.7)
        self.ax.set_title("Drag to select range. Click points to exclude.")
        
        self.scat_phase_all = self.ax.scatter(
            self.x_data, self.phase_data, s=40, c='lightgray', 
            marker='s', edgecolors='gray', picker=True, pickradius=5, zorder=1, label='All Data'
        )
        self.scat_phase_valid = self.ax.scatter([], [], s=40, c='orange', marker='s', zorder=2, label='Used Data')
        self.scat_phase_excl = self.ax.scatter([], [], s=40, c='red', marker='x', zorder=2)
        self.line_fit_phase, = self.ax.plot([], [], '-', color='red', lw=2, zorder=3, alpha=0.8, label='Fit')
        self.ax.legend(loc='upper right')

    def set_global_limits(self):
        # (前回同様の軸調整ロジック)
        if len(self.x_data) > 0:
            x_min, x_max = np.min(self.x_data), np.max(self.x_data)
            margin_x = (x_max - x_min) * 0.1 if x_max != x_min else 1.0
            self.ax.set_xlim(x_min - margin_x, x_max + margin_x)
            self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=False, prune=None))

            y_min, y_max = np.min(self.phase_data), np.max(self.phase_data)
            margin_y = (y_max - y_min) * 0.1 if y_max != y_min else 0.5
            self.ax.set_ylim(y_min - margin_y, y_max + margin_y)

    def on_range_select(self, xmin, xmax):
        self.range_mask = (self.x_data >= xmin) & (self.x_data <= xmax)
        self.update_plot_and_calc()

    def on_point_pick(self, event):
        if event.artist != self.scat_phase_all:
            return
        ind = event.ind
        self.manual_mask[ind] = ~self.manual_mask[ind]
        self.update_plot_and_calc()

    def on_complete(self, event):
        plt.close(self.fig)

    def update_plot_and_calc(self):
        active_mask = self.range_mask & self.manual_mask
        active_indices = np.where(active_mask)[0]
        excluded_mask = self.range_mask & (~self.manual_mask)

        # 表示更新
        self.scat_phase_valid.set_offsets(np.c_[self.x_data[active_mask], self.phase_data[active_mask]])
        self.scat_phase_excl.set_offsets(np.c_[self.x_data[excluded_mask], self.phase_data[excluded_mask]])

        if len(active_indices) < 2:
            self.line_fit_phase.set_data([], [])
            self.ax.set_title("Select at least 2 points")
            self.fig.canvas.draw_idle()
            self.result = None
            return

        # =========================================================
        # ★Analyzerに委譲
        # =========================================================
        self.result = analyzer.run_analysis(self.raw, self.config, list(active_indices))
        # =========================================================

        # Fit線の描画
        x_draw = np.linspace(np.min(self.x_data[active_mask]), np.max(self.x_data[active_mask]), 10)
        self.line_fit_phase.set_data(x_draw, self.result.slope_phase * x_draw + self.result.intercept_phase)

        # タイトル更新 (Analyzerの結果を使用)
        title_text = (
            f"Phase $\\alpha$: {self.result.alpha_phase:.2e} ($R^2$={self.result.r2_phase:.3f})\n"
            f"Amp $\\alpha$: {self.result.alpha_amp:.2e} ($R^2$={self.result.r2_amp:.3f}) | Ratio: {self.result.alpha_ratio:.2f}\n"
            f"kd: {self.result.kd_min:.2f} - {self.result.kd_max:.2f}"
        )
        self.ax.set_title(title_text)
        self.fig.canvas.draw_idle()