from entrypoints.contracts import DiffusivitySummaryRequest
from entrypoints.diffusivity_summary_entry import run_diffusivity_summary

def run_summary():
    target_axis = "z_position"
    print("==========================================")
    print("   TWA Analyzer : Summary Mode")
    print(f"   Target Axis : {target_axis}")
    print("==========================================")
    
    target_dir = input("集計対象の親ディレクトリパスを入力してください > ").strip().strip('"').strip("'")
    
    response = run_diffusivity_summary(
        DiffusivitySummaryRequest(
            target_dir=target_dir,
            summary_type="position",
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