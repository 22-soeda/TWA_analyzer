import numpy as np

def calculate_alpha_from_slope(slope: float, thickness_um: float) -> float:
    """
    TWA振幅プロットの傾きから熱拡散率(m^2/s)を計算
    Theory: slope = -L * sqrt(pi / alpha) 
           => alpha = pi * L^2 / slope^2
    """

    L_meter = thickness_um * 1e-6
    alpha = (np.pi * (L_meter**2)) / (slope**2)
    return alpha

def calculate_kd(freq_array: np.ndarray, alpha: float, thickness_um: float) -> np.ndarray:
    """
    各周波数における kd を計算
    kd = thickness / diffusion_length
       = thickness * sqrt(pi * f / alpha)
    """
    if alpha <= 0 or np.isnan(alpha):
        return np.zeros_like(freq_array)
        
    L_meter = thickness_um * 1e-6
    # freq_array が sqrt(f) なのか f なのか注意が必要。
    # ここでは入力 freq_array は [Hz] 単位の生周波数 f と仮定
    
    kd = L_meter * np.sqrt(np.pi * freq_array / alpha)
    return kd