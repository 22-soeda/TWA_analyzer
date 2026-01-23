from dataclasses import dataclass
import os

@dataclass(frozen=True)
class PathConfig:
    """ファイルパスやディレクトリに関する設定"""
    INPUT_DIR: str = os.path.join(os.getcwd(), "data", "input")
    OUTPUT_DIR: str = os.path.join(os.getcwd(), "data", "output")
    TARGET_EXT: str = ".txt"

@dataclass(frozen=True)
class ColumnConfig:
    """
    入力データの列名（ヘッダー）に関する設定
    ※ データファイルのフォーマットに合わせて変更
    """
    TIME: str = "time"        

    FREQUENCY: str = "freq"  
    SQRT_FREQUENCY: str = "sqrt_TW_freq" 

    AMPLITUDE: str = "amp"  
    AMPLITUDE_SIGMA: str = "amp_sigma" 

    PHASE: str = "theta"       
    PHASE_SIGMA: str = "theta_sigma"  
    
    DCV: str = "DCV"
    DCV_SIGMA: str = "DCV_sigma"
    
    DECAT_RATIO: str = "decay_ratio"

    X_POS: str = "x_pos"
    Y_POS: str = "y_pos"
    Z_POS: str = "z_pos"

    SEPARATOR: str = "\t"

@dataclass(frozen=True)
class AnalysisConfig:
    """解析ロジックやパラメータに関する設定"""
    # 決定係数(R^2)のしきい値。これ未満の場合は信頼性なしと判定する等に使用
    R2_THRESHOLD: float = 0.90
    
    # メタデータに含まれる周波数のキー名（RawData.metadataのキー）
    KEY_FREQUENCY: str = "Frequency"
    
    # メタデータに周波数がない場合のデフォルト周波数 (Hz)
    DEFAULT_FREQUENCY: float = 1.0

    # フィッティングに使用するデータの範囲（例: 0なら全データ、正の値ならその秒数以降など）
    IGNORE_INITIAL_SECONDS: float = 0.0

@dataclass(frozen=True)
class PlotConfig:
    """グラフ描画に関する設定"""
    FIG_SIZE: tuple = (10, 6)
    DPI: int = 100
    FONT_FAMILY: str = "Arial"  # 日本語なら "Meiryo" や "TakaoGothic" など
    
    # プロットの色設定
    COLOR_AMP: str = "blue"
    COLOR_PHASE: str = "orange"
    COLOR_FIT: str = "red"

# 設定インスタンスの生成
paths = PathConfig()
columns = ColumnConfig()
analysis = AnalysisConfig()
plots = PlotConfig()

@dataclass(frozen=True)
class AppConfigClass:
    """アプリケーション全体の設定を統合するクラス"""
    INPUT_DIR: str = paths.INPUT_DIR
    OUTPUT_DIR: str = paths.OUTPUT_DIR
    
    COL_FREQ_SQRT: str = columns.SQRT_FREQUENCY
    COL_AMP: str = columns.AMPLITUDE
    COL_PHASE: str = columns.PHASE

    DEFAULT_THICKNESS_UM: float = 50.0  # デフォルトの試料厚

AppConfig = AppConfigClass()