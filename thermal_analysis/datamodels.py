from dataclasses import dataclass, asdict, field
import pandas as pd
import json
import os
import numpy as np
from typing import List, Dict, Optional

@dataclass
class RawData:
    """読み込んだ生データを保持するクラス"""
    df: pd.DataFrame
    metadata: Dict[str, float]
    filepath: str

@dataclass
class AnalysisResult:
    """解析結果を保持するクラス"""
    filename: str
    samplename: Optional[str] = None

    thickness_um: Optional[float] = None  # 試料厚 (um単位)

    alpha_amp: Optional[float] = None  # 振幅から求めた熱拡散率 (m^2/s)
    alpha_phase: Optional[float] = None  # 位相から求めた熱拡散率 (m^2/s)
    r2_amp: Optional[float] = None       # 振幅フィッティングの決定係数
    r2_phase: Optional[float] = None     # 位相フィッティングの決定係数

    x_position: Optional[float] = None
    y_position: Optional[float] = None
    z_position: Optional[float] = None

    # 解析に使用した範囲情報
    used_indices: List[int] = field(default_factory=list)
    freq_range_min: float = 0.0
    freq_range_max: float = 0.0
    kd_min: Optional[float] = None
    kd_max: Optional[float] = None

    slope_amp: Optional[float] = None
    slope_phase: Optional[float] = None

    def save_to_json(self, output_dir: str):
        """結果をJSONとして保存"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        base_name = os.path.basename(self.filename).rsplit('.', 1)[0]
        save_path = os.path.join(output_dir, f"{base_name}_result.json")
        
        # numpy型などをPython標準型に変換
        data_dict = asdict(self)
        
        # JSONシリアライズ対応のヘルパー
        def default_converter(o):
            if isinstance(o, (np.int64, np.int32)): return int(o)
            if isinstance(o, (np.float64, np.float32)): return float(o)
            return str(o)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=4, default=default_converter)
        print(f"Saved: {save_path}")
        pass

    @staticmethod
    def load_from_json(cls, filepath: str) -> 'AnalysisResult':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)