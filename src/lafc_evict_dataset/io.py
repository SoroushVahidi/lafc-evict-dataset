from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable

import pandas as pd

from .schema import FLOAT_COLUMNS, INTEGER_COLUMNS, STRING_COLUMNS


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_parent(path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def fail_if_output_exists(path: str | Path, *, overwrite: bool, kind: str) -> Path:
    out = Path(path)
    if out.exists() and not overwrite:
        raise FileExistsError(
            f"{kind} already exists at {out}. Pass --overwrite to replace it."
        )
    return out


def ensure_clean_output_dir(path: str | Path, *, overwrite: bool, kind: str) -> Path:
    out = Path(path)
    if out.exists():
        has_files = any(out.iterdir())
        if has_files and overwrite:
            shutil.rmtree(out)
        elif has_files and not overwrite:
            raise FileExistsError(
                f"{kind} already exists and is not empty: {out}. Pass --overwrite to replace files."
            )
    out.mkdir(parents=True, exist_ok=True)
    return out


def _resolve_manifest_paths(manifest_path: Path) -> list[Path]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("files", payload.get("shards", []))
    out: list[Path] = []
    for entry in entries:
        if isinstance(entry, str):
            raw_path = entry
        elif isinstance(entry, dict):
            raw_path = entry.get("path", "")
        else:
            raw_path = ""
        if not raw_path:
            continue
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            resolved_candidate = None
            for base in [manifest_path.parent, *manifest_path.parents]:
                trial = (base / candidate).resolve()
                if trial.exists():
                    resolved_candidate = trial
                    break
            candidate = resolved_candidate or (manifest_path.parent / candidate).resolve()
        out.append(candidate)
    return out


def resolve_candidate_files(input_path: str | Path) -> list[Path]:
    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        if path.suffix.lower() in {".csv", ".parquet"}:
            return [path]
        if path.suffix.lower() == ".json":
            files = _resolve_manifest_paths(path)
            if not files:
                raise ValueError(f"No shard paths found in manifest: {path}")
            return files
        raise ValueError(f"Unsupported input file: {path}")

    files = sorted(
        [
            candidate
            for candidate in path.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in {".csv", ".parquet"}
        ]
    )
    if not files:
        raise ValueError(f"No candidate CSV/Parquet files found under {path}")
    return files


def coerce_candidate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in STRING_COLUMNS:
        if column in out.columns:
            out[column] = out[column].astype("string")
    for column in INTEGER_COLUMNS:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="raise").astype("Int64")
    for column in FLOAT_COLUMNS:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="raise")
    return out


def read_candidate_dataframe(input_path: str | Path) -> pd.DataFrame:
    files = resolve_candidate_files(input_path)
    frames: list[pd.DataFrame] = []
    for path in files:
        if path.suffix.lower() == ".csv":
            frames.append(pd.read_csv(path))
        elif path.suffix.lower() == ".parquet":
            frames.append(pd.read_parquet(path))
    if not frames:
        raise ValueError(f"No readable candidate files found for {input_path}")
    return coerce_candidate_dataframe(pd.concat(frames, ignore_index=True))


def write_table(df: pd.DataFrame, output_path: str | Path, *, overwrite: bool = False) -> Path:
    path = ensure_parent(output_path)
    fail_if_output_exists(path, overwrite=overwrite, kind="Output file")
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
        return path
    if path.suffix.lower() == ".parquet":
        df.to_parquet(path, index=False)
        return path
    raise ValueError(f"Unsupported output format: {path}")


def iter_files(root: str | Path) -> Iterable[Path]:
    path = Path(root)
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*")):
        if child.is_file():
            yield child
