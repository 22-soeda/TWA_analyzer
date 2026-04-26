import os

from config import AppConfig
from freq_sweep_summary import run


def main() -> None:
    print("==========================================")
    print(" Freq Sweep Summary : Interactive Mode")
    print("==========================================")

    default_input = os.path.join(
        os.getcwd(),
        "data_raw",
        "z_freq_sweep_test01_20260421_121456",
        "data_1.csv",
    )
    in_input = input(f"Input Path (Default: {default_input}) > ").strip().strip('"').strip("'")
    input_csv = in_input if in_input else default_input
    input_csv = os.path.abspath(input_csv)

    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_csv}")

    stem = os.path.splitext(os.path.basename(input_csv))[0]
    default_output = os.path.join(AppConfig.OUTPUT_DIR, f"{stem}_pos_freq_summary")
    out_input = input(f"Output Path (Default: {default_output}) > ").strip().strip('"').strip("'")
    output_dir = out_input if out_input else default_output

    tol_input = input("Freq Tolerance Hz (Default: 3.0) > ").strip()
    freq_tolerance_hz = float(tol_input) if tol_input else 3.0

    run(
        input_csv=input_csv,
        output_dir=os.path.abspath(output_dir),
        tolerance_hz=freq_tolerance_hz,
    )


if __name__ == "__main__":
    main()
