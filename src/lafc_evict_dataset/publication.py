from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ASSOCIATED_PAPER_TITLE: Final[str] = "Decision-aligned eviction-value prediction for robust learning-augmented caching"
ASSOCIATED_PAPER_AUTHORS: Final[str] = "Soroush Vahidi."
ASSOCIATED_PAPER_LINK: Final[str] = "https://ssrn.com/abstract=6636732"
ASSOCIATED_PAPER_STATUS: Final[str] = "public preprint; manuscript under peer review."

SYNTHETIC_DISCLAIMER: Final[str] = (
    "This is a synthetic sample release for testing the publication workflow. "
    "It is not suitable for scientific benchmarking."
)

SYNTHETIC_DATA_DISCLAIMER: Final[str] = (
    "This sample release contains synthetic rows only and does not include raw traces or external trace-derived data."
)

HF_DATASET_LICENSE: Final[str] = "mit"
HF_BASE_TAGS: Final[tuple[str, ...]] = (
    "tabular",
    "caching",
    "cache-eviction",
    "learning-augmented-algorithms",
    "counterfactual-supervision",
    "pandas",
    "mlcroissant",
)
HF_SYNTHETIC_TAGS: Final[tuple[str, ...]] = ("synthetic",)
HF_TASK_CATEGORIES: Final[tuple[str, ...]] = ("tabular-regression", "tabular-classification")
HF_DEFAULT_CONFIG_DATA_FILES: Final[tuple[tuple[str, str], ...]] = (
    ("train", "data/candidate_rows/split=train/**/*.parquet"),
    ("validation", "data/candidate_rows/split=val/**/*.parquet"),
    ("test", "data/candidate_rows/split=test/**/*.parquet"),
)

TOKEN_LIKE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b[A-Za-z0-9]{32,}\b"),
)

PUBLIC_TEXT_SUFFIXES: Final[set[str]] = {".md", ".txt", ".json"}


@dataclass(frozen=True)
class ReleaseInventory:
    release_dir: Path
    release_manifest_path: Path
    release_manifest: dict[str, object]
    validation_report_path: Path
    checksums_path: Path
    files: tuple[Path, ...]
    total_files: int
    total_bytes: int
    has_candidate_rows: bool
    has_decision_view: bool
    has_pairwise_view: bool


@dataclass(frozen=True)
class DryRunPlan:
    mode: str
    target: str
    files: tuple[str, ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class HuggingFaceUploadResult:
    repo_id: str
    repo_url: str
    private: bool
    uploaded_files: tuple[str, ...]
    verified_remote_paths: tuple[str, ...]


def publication_template_path(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "publication" / name


def read_publication_template(name: str) -> str:
    return publication_template_path(name).read_text(encoding="utf-8")


def collect_release_inventory(release_dir: str | Path) -> ReleaseInventory:
    release_path = Path(release_dir).resolve()
    manifest_path = release_path / "metadata" / "release_manifest.json"
    validation_report_path = release_path / "metadata" / "validation_report.md"
    checksums_path = release_path / "metadata" / "checksums.sha256"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing release manifest: {manifest_path}")
    if not validation_report_path.exists():
        raise FileNotFoundError(f"Missing release validation report: {validation_report_path}")
    if not checksums_path.exists():
        raise FileNotFoundError(f"Missing release checksums file: {checksums_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = tuple(sorted(path for path in release_path.rglob("*") if path.is_file()))
    total_bytes = sum(path.stat().st_size for path in files)
    rel_files = [path.relative_to(release_path).as_posix() for path in files]
    return ReleaseInventory(
        release_dir=release_path,
        release_manifest_path=manifest_path,
        release_manifest=manifest,
        validation_report_path=validation_report_path,
        checksums_path=checksums_path,
        files=files,
        total_files=len(files),
        total_bytes=total_bytes,
        has_candidate_rows=any(path.startswith("data/candidate_rows/") for path in rel_files),
        has_decision_view="data/decision_view/decision_view.parquet" in rel_files,
        has_pairwise_view="data/pairwise_view/pairwise_view.parquet" in rel_files,
    )


def release_name_from_inventory(inventory: ReleaseInventory) -> str:
    return inventory.release_dir.name


def release_is_synthetic_sample(inventory: ReleaseInventory) -> bool:
    return str(inventory.release_manifest.get("release_type", "")) == "synthetic_sample"


def pretty_name_for_release(dataset_name: str, release_type: str) -> str:
    if release_type == "synthetic_sample":
        return "LAFC-Evict Sample"
    if dataset_name == "lafc-evict-v0.1-open":
        return "LAFC-Evict v0.1 Open"
    if dataset_name == "lafc-evict":
        return "LAFC-Evict"
    return dataset_name.replace("-", " ").title()


def size_category_for_row_count(row_count: int) -> str:
    if row_count < 1_000:
        return "n<1K"
    if row_count < 10_000:
        return "1K<n<10K"
    if row_count < 100_000:
        return "10K<n<100K"
    if row_count < 1_000_000:
        return "100K<n<1M"
    if row_count < 10_000_000:
        return "1M<n<10M"
    if row_count < 100_000_000:
        return "10M<n<100M"
    if row_count < 1_000_000_000:
        return "100M<n<1B"
    if row_count < 10_000_000_000:
        return "1B<n<10B"
    if row_count < 100_000_000_000:
        return "10B<n<100B"
    if row_count < 1_000_000_000_000:
        return "100B<n<1T"
    return "n>1T"


def dataset_tags_for_release(release_type: str) -> tuple[str, ...]:
    if release_type == "synthetic_sample":
        return (*HF_BASE_TAGS, *HF_SYNTHETIC_TAGS)
    return HF_BASE_TAGS


def render_hf_dataset_card_metadata(
    *,
    dataset_name: str,
    release_type: str,
    candidate_row_count: int,
) -> str:
    pretty_name = pretty_name_for_release(dataset_name, release_type)
    size_category = size_category_for_row_count(candidate_row_count)
    tags = dataset_tags_for_release(release_type)

    lines = [
        "---",
        f'pretty_name: {json.dumps(pretty_name)}',
        f'license: {json.dumps(HF_DATASET_LICENSE)}',
        "tags:",
        *[f"- {json.dumps(tag)}" for tag in tags],
        "task_categories:",
        *[f"- {json.dumps(category)}" for category in HF_TASK_CATEGORIES],
        "size_categories:",
        f"- {json.dumps(size_category)}",
        "configs:",
        "- config_name: default",
        "  data_files:",
    ]
    for split, path in HF_DEFAULT_CONFIG_DATA_FILES:
        lines.extend(
            [
                f"  - split: {json.dumps(split)}",
                f"    path: {json.dumps(path)}",
            ]
        )
    lines.append("---")
    return "\n".join(lines)


def render_dataset_card(inventory: ReleaseInventory) -> str:
    template = read_publication_template("HF_DATASET_CARD_TEMPLATE.md")
    return template.format(
        dataset_name=inventory.release_manifest.get("dataset_name", "unknown"),
        version=inventory.release_manifest.get("version", "unknown"),
        release_type=inventory.release_manifest.get("release_type", "unknown"),
        candidate_row_count=inventory.release_manifest.get("row_counts", {}).get("candidate_rows", 0),
        decision_row_count=inventory.release_manifest.get("row_counts", {}).get("decision_view", 0),
        pairwise_row_count=inventory.release_manifest.get("row_counts", {}).get("pairwise_view", 0),
        synthetic_disclaimer=SYNTHETIC_DISCLAIMER if release_is_synthetic_sample(inventory) else "",
        synthetic_data_disclaimer=SYNTHETIC_DATA_DISCLAIMER if release_is_synthetic_sample(inventory) else "",
        release_name=release_name_from_inventory(inventory),
        associated_paper_title=ASSOCIATED_PAPER_TITLE,
        associated_paper_authors=ASSOCIATED_PAPER_AUTHORS,
        associated_paper_link=ASSOCIATED_PAPER_LINK,
        associated_paper_status=ASSOCIATED_PAPER_STATUS,
        hf_metadata_block=render_hf_dataset_card_metadata(
            dataset_name=str(inventory.release_manifest.get("dataset_name", "unknown")),
            release_type=str(inventory.release_manifest.get("release_type", "unknown")),
            candidate_row_count=int(inventory.release_manifest.get("row_counts", {}).get("candidate_rows", 0)),
        ),
    ).strip() + "\n"


def render_zenodo_metadata(inventory: ReleaseInventory) -> dict[str, object]:
    template = json.loads(read_publication_template("ZENODO_METADATA_TEMPLATE.json"))
    metadata = template["metadata"]
    metadata["title"] = f"{inventory.release_manifest.get('dataset_name', 'lafc-evict')} {inventory.release_manifest.get('version', '')}".strip()
    metadata["description"] = (
        SYNTHETIC_DISCLAIMER if release_is_synthetic_sample(inventory) else "Draft LAFC-Evict release metadata."
    )
    metadata["version"] = str(inventory.release_manifest.get("version", "unknown"))
    metadata["keywords"] = [
        "cache eviction",
        "dataset release",
        "counterfactual supervision",
        str(inventory.release_manifest.get("release_type", "unknown")),
    ]
    metadata["related_identifiers"] = [
        {
            "identifier": ASSOCIATED_PAPER_LINK,
            "relation": "isSupplementTo",
            "resource_type": "publication-preprint",
        }
    ]
    metadata["notes"] = (
        f"Associated paper/preprint: {ASSOCIATED_PAPER_TITLE}. "
        f"Status: {ASSOCIATED_PAPER_STATUS}"
    )
    return template


def render_github_release_notes(inventory: ReleaseInventory) -> str:
    template = read_publication_template("GITHUB_RELEASE_NOTES_TEMPLATE.md")
    selected_note = SYNTHETIC_DISCLAIMER if release_is_synthetic_sample(inventory) else ""
    return template.format(
        release_name=release_name_from_inventory(inventory),
        dataset_name=inventory.release_manifest.get("dataset_name", "unknown"),
        version=inventory.release_manifest.get("version", "unknown"),
        release_type=inventory.release_manifest.get("release_type", "unknown"),
        candidate_row_count=inventory.release_manifest.get("row_counts", {}).get("candidate_rows", 0),
        decision_row_count=inventory.release_manifest.get("row_counts", {}).get("decision_view", 0),
        pairwise_row_count=inventory.release_manifest.get("row_counts", {}).get("pairwise_view", 0),
        synthetic_disclaimer=selected_note,
        associated_paper_title=ASSOCIATED_PAPER_TITLE,
        associated_paper_authors=ASSOCIATED_PAPER_AUTHORS,
        associated_paper_link=ASSOCIATED_PAPER_LINK,
        associated_paper_status=ASSOCIATED_PAPER_STATUS,
    ).strip() + "\n"


def render_publication_readme(inventory: ReleaseInventory) -> str:
    lines = [
        f"# {inventory.release_manifest.get('dataset_name', 'unknown')} Publication Bundle",
        "",
        f"- Release name: `{release_name_from_inventory(inventory)}`",
        f"- Version: `{inventory.release_manifest.get('version', 'unknown')}`",
        f"- Release type: `{inventory.release_manifest.get('release_type', 'unknown')}`",
        "",
        "This bundle contains publication metadata only. It does not duplicate release Parquet or other data payloads.",
    ]
    if release_is_synthetic_sample(inventory):
        lines.extend(["", SYNTHETIC_DISCLAIMER, "", SYNTHETIC_DATA_DISCLAIMER])
    return "\n".join(lines).strip() + "\n"


def build_publication_manifest(
    inventory: ReleaseInventory,
    *,
    bundle_dir: str | Path,
) -> dict[str, object]:
    return {
        "dataset_name": inventory.release_manifest.get("dataset_name", "unknown"),
        "version": inventory.release_manifest.get("version", "unknown"),
        "release_type": inventory.release_manifest.get("release_type", "unknown"),
        "source_release_directory": str(inventory.release_dir),
        "total_files_in_release_directory": inventory.total_files,
        "total_bytes_in_release_directory": inventory.total_bytes,
        "checksum_file_path": str(inventory.checksums_path),
        "validation_report_path": str(inventory.validation_report_path),
        "has_candidate_rows": inventory.has_candidate_rows,
        "has_decision_view": inventory.has_decision_view,
        "has_pairwise_view": inventory.has_pairwise_view,
        "intended_huggingface_repo_id": "TODO/replace-with-dataset-repo-id",
        "intended_zenodo_deposition_id": "TODO",
        "intended_github_tag": "TODO",
        "publication_status": "draft_local",
        "bundle_directory": str(Path(bundle_dir).resolve()),
    }


def write_json(path: str | Path, payload: dict[str, object]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def expected_hf_remote_paths(inventory: ReleaseInventory) -> tuple[str, ...]:
    return (
        "README.md",
        "metadata/release_manifest.json",
        "metadata/checksums.sha256",
        "metadata/validation_report.md",
        "data/candidate_rows/",
        "data/decision_view/",
        "data/pairwise_view/",
    )


def token_like_matches(text: str) -> list[str]:
    matches: list[str] = []
    for pattern in TOKEN_LIKE_PATTERNS:
        matches.extend(match.group(0) for match in pattern.finditer(text))
    return sorted(set(matches))


def text_contains_local_absolute_path(text: str) -> bool:
    path_patterns = [
        re.compile(r"(?<![A-Za-z0-9_])/(home|Users|var|tmp|mnt|srv|opt)/[^\s`\"']+"),
        re.compile(r"[A-Za-z]:\\[^\s`\"']+"),
    ]
    return any(pattern.search(text) for pattern in path_patterns)


def validate_public_text_file(path: Path, *, allow_absolute_paths: bool = False) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    matches = token_like_matches(text)
    if matches:
        errors.append(f"Token-like strings detected in {path.name}: {', '.join(matches[:5])}")
    if not allow_absolute_paths and text_contains_local_absolute_path(text):
        errors.append(f"Local absolute path detected in public-facing file: {path}")
    return errors


def ensure_execute_requested(execute: bool, dry_run: bool) -> None:
    if execute and dry_run:
        raise ValueError("Use either --execute or --dry-run, not both.")


def detect_hf_auth_available() -> bool:
    if os.environ.get("HF_TOKEN"):
        return True
    try:
        from huggingface_hub import HfFolder

        return bool(HfFolder.get_token())
    except Exception:
        return False


def hf_api_token() -> str | None:
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    try:
        from huggingface_hub import HfFolder

        return HfFolder.get_token()
    except Exception:
        return None


def detect_zenodo_auth_available() -> bool:
    return bool(os.environ.get("ZENODO_TOKEN"))


def detect_github_auth_available() -> bool:
    if os.environ.get("GITHUB_TOKEN"):
        return True
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    return result.returncode == 0


def plan_huggingface_upload(
    inventory: ReleaseInventory,
    *,
    repo_id: str,
    repo_type: str,
    private: bool,
    allow_public: bool,
    allow_synthetic_public: bool,
    large_folder: bool,
) -> DryRunPlan:
    if not private and not allow_public:
        raise ValueError("Public upload requires --allow-public.")
    if release_is_synthetic_sample(inventory) and not private and not allow_synthetic_public:
        raise ValueError("Public upload of a synthetic sample requires --allow-synthetic-public.")
    return DryRunPlan(
        mode="huggingface",
        target=repo_id,
        files=tuple(path.relative_to(inventory.release_dir).as_posix() for path in inventory.files),
        summary={
            "repo_type": repo_type,
            "private": private,
            "large_folder": large_folder,
            "release_dir": str(inventory.release_dir),
        },
    )


def execute_huggingface_upload(
    inventory: ReleaseInventory,
    *,
    repo_id: str,
    repo_type: str,
    private: bool,
    large_folder: bool,
) -> HuggingFaceUploadResult:
    token = hf_api_token()
    if not token:
        raise ValueError("Execute mode requires HF_TOKEN or a pre-authenticated Hugging Face CLI session.")

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(repo_id=repo_id, repo_type=repo_type, private=private, exist_ok=True)

    if large_folder and hasattr(api, "upload_large_folder"):
        api.upload_large_folder(
            repo_id=repo_id,
            repo_type=repo_type,
            folder_path=str(inventory.release_dir),
        )
    else:
        api.upload_folder(
            repo_id=repo_id,
            repo_type=repo_type,
            folder_path=str(inventory.release_dir),
        )

    repo_info = api.repo_info(repo_id=repo_id, repo_type=repo_type)
    remote_files = tuple(sorted(api.list_repo_files(repo_id=repo_id, repo_type=repo_type)))
    expected = expected_hf_remote_paths(inventory)
    verified: list[str] = []
    for expected_path in expected:
        if expected_path.endswith("/"):
            prefix = expected_path
            if not any(path.startswith(prefix) for path in remote_files):
                raise FileNotFoundError(f"Missing expected remote path prefix: {expected_path}")
            verified.append(expected_path)
        else:
            if expected_path not in remote_files:
                raise FileNotFoundError(f"Missing expected remote file: {expected_path}")
            verified.append(expected_path)

    private_flag = bool(getattr(repo_info, "private", private))
    return HuggingFaceUploadResult(
        repo_id=repo_id,
        repo_url=f"https://huggingface.co/datasets/{repo_id}",
        private=private_flag,
        uploaded_files=remote_files,
        verified_remote_paths=tuple(verified),
    )


def plan_zenodo_upload(
    bundle_dir: Path,
    *,
    sandbox: bool,
    include_release_files: bool,
    release_dir: Path | None = None,
) -> DryRunPlan:
    files = sorted(
        path.relative_to(bundle_dir).as_posix()
        for path in bundle_dir.rglob("*")
        if path.is_file()
    )
    if include_release_files and release_dir is not None:
        files.extend(
            sorted(
                f"release::{path.relative_to(release_dir).as_posix()}"
                for path in release_dir.rglob("*")
                if path.is_file()
            )
        )
    return DryRunPlan(
        mode="zenodo",
        target="sandbox" if sandbox else "production",
        files=tuple(files),
        summary={
            "bundle_dir": str(bundle_dir),
            "include_release_files": include_release_files,
        },
    )


def plan_github_release(
    *,
    repo: str,
    tag: str,
    title: str,
    notes_file: Path,
    assets: list[Path],
    prerelease: bool,
) -> DryRunPlan:
    if not notes_file.exists():
        raise FileNotFoundError(f"Notes file does not exist: {notes_file}")
    missing_assets = [str(path) for path in assets if not path.exists()]
    if missing_assets:
        raise FileNotFoundError("Missing GitHub release assets: " + ", ".join(missing_assets))
    return DryRunPlan(
        mode="github",
        target=repo,
        files=tuple([notes_file.name, *[path.name for path in assets]]),
        summary={
            "tag": tag,
            "title": title,
            "prerelease": prerelease,
            "recommend_prerelease": ("sample" in tag.lower() or "rc" in tag.lower()),
        },
    )
