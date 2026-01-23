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

    def save_input_data(self, output_dir: str):
        """
        RawDataを再利用可能なJSON形式で保存
        input_data.json として保存します
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # DataFrameをJSONシリアライズ可能な辞書形式(split)に変換
        # split形式: {'index': [...], 'columns': [...], 'data': [[...], ...]}
        df_dict = self.df.to_dict(orient='split')
        
        save_data = {
            "metadata": self.metadata,
            "filepath": self.filepath,
            "dataframe": df_dict
        }

        save_path = os.path.join(output_dir, "input_data.json")
        
        def default_converter(o):
            if isinstance(o, (np.int64, np.int32)): return int(o)
            if isinstance(o, (np.float64, np.float32)): return float(o)
            return str(o)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False, default=default_converter)
        print(f"Saved Input Data: {save_path}")

@dataclass
class AnalysisResult:
    """解析結果を保持するクラス"""
    filename: str
    samplename: Optional[str] = None

    thickness_um: Optional[float] = None  # 試料厚 (um単位)

    # --- Phase results ---
    alpha_phase: Optional[float] = None
    r2_phase: Optional[float] = None
    slope_phase: Optional[float] = None
    intercept_phase: Optional[float] = None

    # --- Amplitude results ---
    alpha_amp: Optional[float] = None
    r2_amp: Optional[float] = None
    slope_amp: Optional[float] = None
    intercept_amp: Optional[float] = None

    alpha_ratio: Optional[float] = None

    #--- Position ---
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    z_position: Optional[float] = None


    #--- analysis range ---
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
            
        save_path = os.path.join(output_dir, "results.json")

        data_dict = asdict(self)

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