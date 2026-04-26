from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TwaAnalyzerRequest:
    input_path: str
    output_dir: str
    recursive: bool = True


@dataclass
class TwaAnalyzerResponse:
    processed_files: int
    saved_cases: int
    skipped_cases: int
    errors: List[str] = field(default_factory=list)


@dataclass
class DiffusivitySummaryRequest:
    target_dir: str
    summary_type: str
    confidence_percent: float = 95.0


@dataclass
class DiffusivitySummaryResponse:
    output_files: List[str]
    row_count: int
    warnings: List[str] = field(default_factory=list)


@dataclass
class PlotterRequest:
    target_dir: str
    config_path: Optional[str] = None
    include_errorbars: bool = False
    interactive_fit_csv: Optional[str] = None


@dataclass
class PlotterResponse:
    output_files: List[str]
    plotted_series_count: int
    used_labels: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

