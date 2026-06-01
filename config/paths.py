from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


# -------------------
# Data folders
# -------------------

DATA_DIR = ROOT_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

CLEAN_DATA_DIR = DATA_DIR / "clean"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

FACTOR_DATA_DIR = DATA_DIR / "factors"


# -------------------
# Index data
# -------------------

INDEX_DIR = DATA_DIR / "indices"

SECTOR_DIR = DATA_DIR / "sector"


# -------------------
# Backtest outputs
# -------------------

RESULTS_DIR = ROOT_DIR / "results"

LOG_DIR = ROOT_DIR / "logs"

REPORT_DIR = ROOT_DIR / "reports"


# -------------------
# Create folders automatically
# -------------------

for p in [
    DATA_DIR,
    RAW_DATA_DIR,
    CLEAN_DATA_DIR,
    PROCESSED_DATA_DIR,
    FACTOR_DATA_DIR,
    INDEX_DIR,
    SECTOR_DIR,
    RESULTS_DIR,
    LOG_DIR,
    REPORT_DIR
]:
    p.mkdir(parents=True, exist_ok=True)

