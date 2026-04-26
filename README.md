# TWA Analyzer

TWA測定データの解析とサマリー生成、CSV可視化を行うプロジェクトです。  
現在は以下の3窓口で機能を整理しています。

- TWA測定アナライザ
- 熱拡散率情報サマリー
- matplotlibプロッタ

## 必要環境

- `uv`
- Python 3.10 以上（推奨）
- 主要ライブラリ
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `scipy`

初回セットアップ例:

```bash
uv venv
uv pip install numpy pandas matplotlib scipy
```

## 使い方

作業ディレクトリをプロジェクトルート (`TWA_analyzer`) に合わせて実行してください。

### 1) TWA測定アナライザ窓口

インタラクティブに範囲選択して、解析結果と図を出力します。

```bash
uv run TWA_cal.py
```

実行時に入力:

- `Input Path`: `.txt` データのファイルまたはディレクトリ
- `Output Path`: 結果の出力先ディレクトリ

主な出力（各ケースディレクトリ）:

- `results.json`
- `input_data.json`
- `raw_data.txt`
- `phase_plot.png`
- `amplitude_plot.png`

### 2) 熱拡散率情報サマリー窓口

#### 2-1. 位置サマリー（z と alpha）

```bash
uv run TWA_pos_sammary.py
```

出力例:

- `summary_results.json`
- `summary_results.csv`
- `summary_pos_alpha.png`
- `summary_pos_ratio.png`

#### 2-2. 厚みサマリー（z と thickness）

```bash
uv run TWA_thickness_sammary.py
```

出力例:

- `summary_thickness.json`
- `summary_z_vs_thickness.png`

#### 2-3. 信頼区間付きサマリー

```bash
uv run alpha_err.py
```

`alpha_err.py` 内の設定:

- `TARGET_PARENT_DIR`: 解析済みケース群の親ディレクトリ
- `CONFIDENCE_PERCENT`: 信頼区間（例: `95.0`）

出力例:

- `thermal_diffusivity_summary.csv`

### 3) matplotlibプロッタ窓口

#### 3-1. CSV重ね描き（散布図）

```bash
uv run plot_marge.py
```

#### 3-2. エラーバー付き重ね描き

```bash
uv run plot_merge_err.py
```

#### 3-3. 単一CSVのインタラクティブfit

```bash
uv run partical_fit.py
```

## プロッタの設定（config）

`plot_marge.py` / `plot_merge_err.py` / `partical_fit.py` は、対象ディレクトリ内の `config.json` を参照できます。  
以下の仕様に対応しています。

- ラベル自動解決: `config指定 > CSVヘッダー推定 > デフォルト`
- 軸範囲自動設定: データ範囲をロバストに算出し、tickに整合するよう調整
- `headers` 指定があれば優先的に列を使用

設定例:

```json
{
  "xlabel": "Z Position [um]",
  "ylabel": "Thermal Diffusivity [m^2/s]",
  "headers": {
    "x": "z",
    "y": "alpha",
    "y_upper": "alpha_upper_95%",
    "y_lower": "alpha_lower_95%"
  },
  "plots": [
    {
      "csv_file": "sample1.csv",
      "legend": "Sample 1",
      "shift_z": 0.0,
      "shift_y": 0.0
    }
  ]
}
```

## 注意点

- `partical_fit.py` はGUI表示を使うため、実行環境でmatplotlibの表示バックエンドが必要です。
- 既存のファイル名・出力形式互換を優先しているため、スクリプト名は従来のまま維持しています。

