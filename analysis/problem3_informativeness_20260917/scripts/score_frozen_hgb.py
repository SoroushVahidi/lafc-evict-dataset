from __future__ import annotations

import pickle
import time
import warnings
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "analysis" / "problem3_informativeness_20260917" / "outputs"
SOURCE_REPO = Path("/home/soroush/projects/lafc-evict-dataset/repo")
CANDIDATE_DIR = (
    SOURCE_REPO
    / "release/lafc-evict-v0.1-open-current-contract-preserved/data/candidate_rows"
)
MODEL_DIR = Path("/home/soroush/projects/augmented-caching/repo/models")

KEY = [
    "trace_name",
    "trace_family",
    "dataset_source",
    "capacity",
    "horizon",
    "decision_id",
    "decision_t",
    "decision_chunk_id",
    "split",
]

MODEL_BY_HORIZON = {
    4: MODEL_DIR / "evict_value_wulver_v1_h4_hist_gb.pkl",
    8: MODEL_DIR / "evict_value_wulver_v1_h8_hist_gb.pkl",
    16: MODEL_DIR / "evict_value_wulver_v1_h16_hist_gb.pkl",
}


def _load_models() -> dict[int, dict[str, object]]:
    models = {}
    for horizon, path in MODEL_BY_HORIZON.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with path.open("rb") as f:
                obj = pickle.load(f)
        models[horizon] = obj
    return models


def _horizon_from_path(path: Path) -> int:
    for part in path.parts:
        if part.startswith("horizon="):
            return int(part.split("=", 1)[1])
    raise ValueError(f"cannot infer horizon from {path}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    models = _load_models()
    feature_columns = list(next(iter(models.values()))["feature_columns"])
    columns = [*KEY, "candidate_page_id", "y_loss", *feature_columns]

    selected_frames = []
    paths = sorted(CANDIDATE_DIR.glob("split=*/trace_family=*/capacity=*/horizon=*/candidate_rows.parquet"))
    for i, path in enumerate(paths, start=1):
        horizon = _horizon_from_path(path)
        model = models[horizon]["estimator"]
        df = pd.read_parquet(path, columns=columns)
        scores = model.predict(df[feature_columns])
        df = df.assign(_score=scores)
        df["_min_y_loss"] = df.groupby(KEY, sort=False)["y_loss"].transform("min")
        selected = (
            df.sort_values([*KEY, "_score", "candidate_page_id"])
            .drop_duplicates(KEY, keep="first")
            [[*KEY, "candidate_page_id", "y_loss", "_min_y_loss"]]
            .rename(
                columns={
                    "candidate_page_id": "selected_candidate_page_id",
                    "y_loss": "selected_y_loss",
                    "_min_y_loss": "min_y_loss",
                }
            )
        )
        selected["realized_regret"] = selected["selected_y_loss"] - selected["min_y_loss"]
        selected["optimal_selection_rate"] = (
            selected["selected_y_loss"] == selected["min_y_loss"]
        ).astype(float)
        selected_frames.append(selected)
        if i % 12 == 0 or i == len(paths):
            print(f"scored {i}/{len(paths)} files in {time.time() - t0:.1f}s", flush=True)

    out = pd.concat(selected_frames, ignore_index=True)
    out_path = OUT / "frozen_hgb_outcomes.parquet"
    out.to_parquet(out_path, index=False)
    print(f"wrote {len(out)} frozen-HGB decision outcomes to {out_path}")


if __name__ == "__main__":
    main()
