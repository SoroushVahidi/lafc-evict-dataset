from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from lafc_evict_dataset.views import build_decision_view

    candidate_csv = ROOT / "examples" / "tiny_candidate_rows.csv"
    df = pd.read_csv(candidate_csv)
    decision_view = build_decision_view(df)

    lru_rows = df[df["candidate_is_lru_victim"] == 1].copy()
    lru_rows["best_y_loss"] = lru_rows.groupby(["trace_name", "capacity", "horizon", "decision_id"])["y_loss"].transform("min")
    lru_rows["regret"] = lru_rows["y_loss"] - lru_rows["best_y_loss"]

    print("Decision view:")
    print(decision_view.to_string(index=False))
    print()
    print(f"Mean LRU regret on the tiny synthetic sample: {lru_rows['regret'].mean():.3f}")


if __name__ == "__main__":
    main()
