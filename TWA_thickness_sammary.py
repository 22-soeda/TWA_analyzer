import os

from entrypoints.contracts import DiffusivitySummaryRequest
from entrypoints.diffusivity_summary_entry import run_diffusivity_summary

def run_summary():
    x_axis = "z_position"
    y_axis = "thickness_um"
    print("==========================================")
    print("   TWA Analyzer : Thickness Summary Mode")
    print(f"   X Axis : {x_axis}")
    print(f"   Y Axis : {y_axis}")
    print("==========================================")
    
    default_dir = os.path.join(os.getcwd(), "data", "output")
    input_dir = input(f"集計対象の親ディレクトリパスを入力してください (Default: {default_dir}) > ").strip().strip('"').strip("'")
    target_dir = input_dir if input_dir else default_dir
    
    response = run_diffusivity_summary(
        DiffusivitySummaryRequest(
            target_dir=target_dir,
            summary_type="thickness",
        )
    )
    print(f"集計データ数: {response.row_count}")
    for output in response.output_files:
        print(f"Saved: {output}")
    for warning in response.warnings:
        print(f"[Warning] {warning}")
    print("\n=== 集計完了 ===")

if __name__ == "__main__":
    run_summary()