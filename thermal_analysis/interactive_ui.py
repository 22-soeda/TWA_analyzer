import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
import matplotlib.ticker as ticker
import numpy as np
from .datamodels import RawData, AnalysisResult
from . import fitting, physics

class TWAInteractivePlotter:
    def __init__(self, raw_data: RawData, config, on_save_callback=None):
        self.raw = raw_data
        self.config = config
        self.result = None 
        
        # 外部から注入される保存処理関数
        self.on_save_callback = on_save_callback

        # --- データ準備 ---
        self.x_data = raw_data.df[config.COL_FREQ_SQRT].values # sqrt(f)
        self.amp_data = raw_data.df[config.COL_AMP].values
        self.phase_data = raw_data.df[config.COL_PHASE].values # Phase (rad)

        # 解析用 Yデータ (振幅は対数)
        self.y_amp_log = np.log(self.amp_data)
        
        self.thickness = raw_data.metadata.get("試料厚", config.DEFAULT_THICKNESS_UM)

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
        
        # --- ボタン配置 ---
        ax_save = plt.axes([0.7, 0.05, 0.1, 0.075])
        self.btn_save = Button(ax_save, 'Save JSON')
        self.btn_save.on_clicked(self.save_result)

        ax_comp = plt.axes([0.81, 0.05, 0.1, 0.075])
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
            marker='s', edgecolors='gray', picker=True, pickradius=5, zorder=1, label='Phase (All)'
        )
        self.scat_phase_valid = self.ax.scatter([], [], s=40, c='orange', marker='s', zorder=2, label='Phase (Valid)')
        self.scat_phase_excl = self.ax.scatter([], [], s=40, c='red', marker='x', zorder=2)
        self.line_fit_phase, = self.ax.plot([], [], '-', color='red', lw=2, zorder=3, alpha=0.8, label='Fit (Phase)')
        self.ax.legend(loc='upper right')

    def set_global_limits(self):
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

        self.scat_phase_valid.set_offsets(np.c_[self.x_data[active_mask], self.phase_data[active_mask]])
        self.scat_phase_excl.set_offsets(np.c_[self.x_data[excluded_mask], self.phase_data[excluded_mask]])

        if len(active_indices) < 2:
            self.line_fit_phase.set_data([], [])
            self.ax.set_title("Select at least 2 points")
            self.fig.canvas.draw_idle()
            return

        # 1. Phase Fitting
        fit_phase = fitting.linear_regression_subset(self.x_data, self.phase_data, list(active_indices))
        alpha_phase = physics.calculate_alpha_from_slope(fit_phase.slope, self.thickness) 
        
        # 2. Amplitude Fitting (Calculation only)
        fit_amp = fitting.linear_regression_subset(self.x_data, self.y_amp_log, list(active_indices))
        alpha_amp = physics.calculate_alpha_from_slope(fit_amp.slope, self.thickness)
        
        # 3. kd Calculation
        freq_hz = self.x_data[active_indices] ** 2
        kd_values = physics.calculate_kd(freq_hz, alpha_phase, self.thickness)
        kd_min, kd_max = (np.min(kd_values), np.max(kd_values))

        # Draw Line
        x_draw = np.linspace(np.min(self.x_data[active_mask]), np.max(self.x_data[active_mask]), 10)
        self.line_fit_phase.set_data(x_draw, fit_phase.slope * x_draw + fit_phase.intercept)

        # Ratio Calculation
        if alpha_amp > 0 and alpha_phase > 0:
            val1, val2 = alpha_amp, alpha_phase
            alpha_ratio = min(val1, val2) / max(val1, val2)
        else:
            alpha_ratio = 0.0
        
        title_text = (
            f"Phase $\\alpha$: {alpha_phase:.2e} ($R^2$={fit_phase.r2:.3f})\n"
            f"Amp $\\alpha$: {alpha_amp:.2e} ($R^2$={fit_amp.r2:.3f}) | Ratio: {alpha_ratio:.2f}\n"
            f"kd (Phase): {kd_min:.2f} - {kd_max:.2f}"
        )
        self.ax.set_title(title_text)
        self.fig.canvas.draw_idle()

        # Update Result Object
        self.result = AnalysisResult(
            filename=self.raw.filepath,
            thickness_um=self.thickness,
            
            alpha_amp=alpha_amp,
            r2_amp=fit_amp.r2,
            slope_amp=fit_amp.slope,
            intercept_amp=fit_amp.intercept,
            
            alpha_phase=alpha_phase,
            r2_phase=fit_phase.r2,
            slope_phase=fit_phase.slope,
            intercept_phase=fit_phase.intercept,
            
            alpha_ratio=alpha_ratio,
            
            used_indices=active_indices.tolist(),
            freq_range_min=float(np.min(self.x_data[active_mask])),
            freq_range_max=float(np.max(self.x_data[active_mask])),
            kd_min=float(kd_min),
            kd_max=float(kd_max)
        )

    def save_result(self, event):
        """保存ボタンクリック時の処理"""
        if self.result and self.on_save_callback:
            # TWA_calから渡されたコールバックを実行
            self.on_save_callback(self.raw, self.result)
        elif not self.on_save_callback:
            print("[System Error] 保存コールバックが設定されていません。")