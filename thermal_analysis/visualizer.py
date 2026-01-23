import matplotlib.pyplot as plt
import numpy as np
from .datamodels import RawData, AnalysisResult

def plot_diagnostic(raw: RawData, res: AnalysisResult, config, save_path=None):
    """
    1データの詳細解析図（ボード線図 + フィッティング）を描画
    """
    df = raw.df
    x = df[config.COL_FREQ].values # sqrt(f)
    y_amp = np.log(df[config.COL_AMP].values) # ln(A)
    y_phase = df[config.COL_PHASE].values # Phase
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f"Analysis: {raw.filepath}", fontsize=14)
    
    # 左上: 振幅 生データとフィッティング
    axes[0,0].scatter(x, y_amp, s=10, label='Data')
    axes[0,0].plot(x, res.slope_amp * x + (y_amp[0] - res.slope_amp*x[0]), 'r-', label=f'Fit (R2={res.r2_amp:.4f})')
    axes[0,0].set_title(f"Amplitude Fitting (alpha={res.alpha_amp:.2e})")
    axes[0,0].set_ylabel("ln(Amplitude)")
    axes[0,0].grid(True)
    
    # 左下: 位相 生データとフィッティング
    axes[1,0].scatter(x, y_phase, s=10, color='orange', label='Data')
    axes[1,0].plot(x, res.slope_phase * x + (y_phase[0] - res.slope_phase*x[0]), 'r-', label=f'Fit (R2={res.r2_phase:.4f})')
    axes[1,0].set_title(f"Phase Fitting (alpha={res.alpha_phase:.2e})")
    axes[1,0].set_xlabel("sqrt(Frequency)")
    axes[1,0].set_ylabel("Phase [rad]")
    axes[1,0].grid(True)

    # 右側: テキスト情報
    axes[0,1].axis('off')
    axes[1,1].axis('off')
    info_text = (
        f"Filename: {res.filename}\n"
        f"Thickness: {raw.metadata.get('試料厚', 'N/A')} um\n"
        f"Alpha (Amp): {res.alpha_amp:.3e} m2/s\n"
        f"Alpha (Phase): {res.alpha_phase:.3e} m2/s\n"
    )
    axes[0,1].text(0.1, 0.5, info_text, fontsize=12)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

def plot_spatial_distribution(results: list[AnalysisResult]):
    """
    複数の解析結果から、位置 vs 熱拡散率のプロットを作成
    """
    # x位置でソート
    results.sort(key=lambda r: r.x_position if r.x_position else 0)
    
    xs = [r.x_position for r in results]
    alphas_amp = [r.alpha_amp for r in results]
    alphas_phase = [r.alpha_phase for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.plot(xs, alphas_amp, 'o-', label='Alpha (Amp)')
    plt.plot(xs, alphas_phase, 's-', label='Alpha (Phase)')
    
    plt.xlabel('Position (x)')
    plt.ylabel('Thermal Diffusivity [m^2/s]')
    plt.title('Spatial Distribution of Thermal Diffusivity')
    plt.legend()
    plt.grid(True)
    plt.show()