from entrypoints.contracts import DiffusivitySummaryRequest
from entrypoints.diffusivity_summary_entry import run_diffusivity_summary

# ============================================================
# ユーザー設定セクション (ここを変更して実行してください)
# ============================================================
# 解析対象のフォルダ群が格納されている親ディレクトリのパス
# (Windowsの場合はパスの前に r を付けるか、\\ で区切ってください)
TARGET_PARENT_DIR = r"C:\Users\YourName\Documents\Research\Data"

# 計算に使用する信頼区間 (%)
# 例: 95 -> 95%信頼区間 (両側), 90 -> 90%信頼区間
CONFIDENCE_PERCENT = 95.0
# ============================================================

def create_thermal_diffusivity_summary():
    response = run_diffusivity_summary(
        DiffusivitySummaryRequest(
            target_dir=TARGET_PARENT_DIR,
            summary_type="confidence",
            confidence_percent=CONFIDENCE_PERCENT,
        )
    )
    if response.row_count == 0:
        print("有効な解析データが見つかりませんでした。")
        return
    print("-" * 30)
    for output in response.output_files:
        print(f"解析完了。サマリーを '{output}' として保存しました。")
    print(f"行数: {response.row_count}")
    for warning in response.warnings:
        print(f"[Warning] {warning}")

if __name__ == "__main__":
    create_thermal_diffusivity_summary()