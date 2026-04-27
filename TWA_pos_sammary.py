from entrypoints.contracts import DiffusivitySummaryRequest
from entrypoints.diffusivity_summary_entry import run_diffusivity_summary
from pathlib import Path


def _find_results_json_recursively(target_dir: Path) -> list[Path]:
    return sorted(p for p in target_dir.rglob("results.json") if p.is_file())

def run_summary():
    target_axis = "z_position"
    print("==========================================")
    print("   TWA Analyzer : Summary Mode")
    print(f"   Target Axis : {target_axis}")
    print("==========================================")
    
    target_dir_str = input("集計対象の親ディレクトリパスを入力してください > ").strip().strip('"').strip("'")
    target_dir = Path(target_dir_str).expanduser().resolve()
    result_files = _find_results_json_recursively(target_dir)

    if not result_files:
        print(f"[Warning] results.json が見つかりません: {target_dir}")
        return

    print(f"検出した results.json 数: {len(result_files)}")
    
    response = run_diffusivity_summary(
        DiffusivitySummaryRequest(
            target_dir=str(target_dir),
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