from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol

ASSOCIATED_PAPER_TITLE: Final[str] = "Decision-aligned eviction-value prediction for robust learning-augmented caching"
ASSOCIATED_PAPER_AUTHORS: Final[str] = "Soroush Vahidi."
ASSOCIATED_PAPER_LINK: Final[str] = "https://ssrn.com/abstract=6636732"
ASSOCIATED_PAPER_STATUS: Final[str] = "public preprint; manuscript under peer review."
ASSOCIATED_PAPER_CITATION: Final[str] = "Available at SSRN 6636732."
ZENODO_SANDBOX_BASE_URL: Final[str] = "https://sandbox.zenodo.org"
ZENODO_PRODUCTION_BASE_URL: Final[str] = "https://zenodo.org"
ZENODO_SAFE_BUNDLE_FILENAMES: Final[tuple[str, ...]] = (
    "README.md",
    "dataset_card.md",
    "github_release_notes.md",
    "publication_manifest.json",
    "zenodo_metadata.json",
)

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
PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS: Final[dict[str, str]] = {
    "release_manifest": "metadata/release_manifest.json",
    "checksums": "metadata/checksums.sha256",
    "validation_report": "metadata/validation_report.md",
}


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
    has_pairwise_sample: bool


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


@dataclass(frozen=True)
class ZenodoExecutionResult:
    target: str
    deposition_id: int
    concept_record_id: str | None
    metadata_title: str
    uploaded_filenames: tuple[str, ...]
    links: dict[str, str]
    doi: str | None
    prereserved_doi: str | None
    state: str | None
    submitted: bool | None


@dataclass(frozen=True)
class ZenodoManifestFile:
    path: str
    bytes: int
    sha256: str
    md5: str
    role: str


@dataclass(frozen=True)
class ZenodoFileManifest:
    manifest_version: str
    dataset: str
    version: str
    release_root_name: str
    expected_file_count: int
    expected_total_bytes: int
    files: tuple[ZenodoManifestFile, ...]


@dataclass(frozen=True)
class ZenodoDraftPlan:
    target: str
    metadata_path: Path
    manifest_path: Path
    release_dir: Path
    metadata: dict[str, object]
    file_manifest: ZenodoFileManifest
    operations: tuple[str, ...]


@dataclass(frozen=True)
class ZenodoDraftExecutionResult:
    target: str
    deposition_id: int
    concept_record_id: str | None
    metadata_title: str
    uploaded_filenames: tuple[str, ...]
    links: dict[str, str]
    doi: str | None
    prereserved_doi: str | None
    state: str | None
    submitted: bool | None
    total_bytes: int


class ResponseLike(Protocol):
    status_code: int
    text: str

    def json(self) -> Any:
        ...


class SessionLike(Protocol):
    def post(self, url: str, **kwargs: Any) -> ResponseLike:
        ...

    def put(self, url: str, **kwargs: Any) -> ResponseLike:
        ...

    def get(self, url: str, **kwargs: Any) -> ResponseLike:
        ...


def publication_template_path(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "publication" / name


def read_publication_template(name: str) -> str:
    return publication_template_path(name).read_text(encoding="utf-8")


def manifest_dataset_name(manifest: dict[str, object]) -> str:
    return str(manifest.get("dataset_name") or manifest.get("dataset_id") or "unknown")


def manifest_row_counts(manifest: dict[str, object]) -> dict[str, int]:
    row_counts: dict[str, int] = {}
    raw_row_counts = manifest.get("row_counts", {})
    if isinstance(raw_row_counts, dict):
        for key, value in raw_row_counts.items():
            if value is not None:
                row_counts[str(key)] = int(value)

    legacy_mappings = {
        "candidate_rows": "candidate_row_count",
        "decision_view": "decision_row_count",
        "pairwise_view": "pairwise_view_row_count",
        "pairwise_sample": "pairwise_sample_row_count",
    }
    for nested_key, flat_key in legacy_mappings.items():
        if nested_key not in row_counts and manifest.get(flat_key) is not None:
            row_counts[nested_key] = int(manifest[flat_key])
    return row_counts


def manifest_pairwise_row_count(manifest: dict[str, object]) -> int:
    row_counts = manifest_row_counts(manifest)
    return int(row_counts.get("pairwise_view", row_counts.get("pairwise_sample", 0)))


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
        has_pairwise_sample="data/pairwise_sample/pairwise_sample.parquet" in rel_files,
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
    license_id: str = HF_DATASET_LICENSE,
    pretty_name: str | None = None,
    extra_tags: tuple[str, ...] = (),
    configs: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] | None = None,
) -> str:
    pretty_name = pretty_name or pretty_name_for_release(dataset_name, release_type)
    size_category = size_category_for_row_count(candidate_row_count)
    tags = tuple(dict.fromkeys((*dataset_tags_for_release(release_type), *extra_tags)))

    lines = [
        "---",
        f'pretty_name: {json.dumps(pretty_name)}',
        f'license: {json.dumps(license_id)}',
        "tags:",
        *[f"- {json.dumps(tag)}" for tag in tags],
        "task_categories:",
        *[f"- {json.dumps(category)}" for category in HF_TASK_CATEGORIES],
        "size_categories:",
        f"- {json.dumps(size_category)}",
        "configs:",
    ]
    config_entries = configs or (("default", HF_DEFAULT_CONFIG_DATA_FILES),)
    for config_name, data_files in config_entries:
        lines.extend([f"- config_name: {json.dumps(config_name)}", "  data_files:"])
        for split, path in data_files:
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
    row_counts = manifest_row_counts(inventory.release_manifest)
    return template.format(
        dataset_name=manifest_dataset_name(inventory.release_manifest),
        version=inventory.release_manifest.get("version", "unknown"),
        release_type=inventory.release_manifest.get("release_type", "unknown"),
        candidate_row_count=row_counts.get("candidate_rows", 0),
        decision_row_count=row_counts.get("decision_view", 0),
        pairwise_row_count=manifest_pairwise_row_count(inventory.release_manifest),
        synthetic_disclaimer=SYNTHETIC_DISCLAIMER if release_is_synthetic_sample(inventory) else "",
        synthetic_data_disclaimer=SYNTHETIC_DATA_DISCLAIMER if release_is_synthetic_sample(inventory) else "",
        release_name=release_name_from_inventory(inventory),
        associated_paper_title=ASSOCIATED_PAPER_TITLE,
        associated_paper_authors=ASSOCIATED_PAPER_AUTHORS,
        associated_paper_link=ASSOCIATED_PAPER_LINK,
        associated_paper_status=ASSOCIATED_PAPER_STATUS,
        hf_metadata_block=render_hf_dataset_card_metadata(
            dataset_name=manifest_dataset_name(inventory.release_manifest),
            release_type=str(inventory.release_manifest.get("release_type", "unknown")),
            candidate_row_count=int(row_counts.get("candidate_rows", 0)),
        ),
    ).strip() + "\n"


def render_zenodo_metadata(inventory: ReleaseInventory) -> dict[str, object]:
    template = json.loads(read_publication_template("ZENODO_METADATA_TEMPLATE.json"))
    metadata = template["metadata"]
    metadata["title"] = f"{manifest_dataset_name(inventory.release_manifest)} {inventory.release_manifest.get('version', '')}".strip()
    if release_is_synthetic_sample(inventory):
        metadata["description"] = " ".join(
            [
                SYNTHETIC_DISCLAIMER,
                SYNTHETIC_DATA_DISCLAIMER,
                f"Associated manuscript: {ASSOCIATED_PAPER_TITLE}",
                f"Author: {ASSOCIATED_PAPER_AUTHORS}",
                ASSOCIATED_PAPER_CITATION,
                f"Status: {ASSOCIATED_PAPER_STATUS}",
            ]
        )
    else:
        metadata["description"] = "Draft LAFC-Evict release metadata."
    metadata["version"] = str(inventory.release_manifest.get("version", "unknown"))
    metadata["license"] = "MIT"
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
        f"Author: {ASSOCIATED_PAPER_AUTHORS} "
        f"{ASSOCIATED_PAPER_CITATION} "
        f"Status: {ASSOCIATED_PAPER_STATUS}"
    )
    return template


def render_github_release_notes(inventory: ReleaseInventory) -> str:
    template = read_publication_template("GITHUB_RELEASE_NOTES_TEMPLATE.md")
    selected_note = SYNTHETIC_DISCLAIMER if release_is_synthetic_sample(inventory) else ""
    row_counts = manifest_row_counts(inventory.release_manifest)
    return template.format(
        release_name=release_name_from_inventory(inventory),
        dataset_name=manifest_dataset_name(inventory.release_manifest),
        version=inventory.release_manifest.get("version", "unknown"),
        release_type=inventory.release_manifest.get("release_type", "unknown"),
        candidate_row_count=row_counts.get("candidate_rows", 0),
        decision_row_count=row_counts.get("decision_view", 0),
        pairwise_row_count=manifest_pairwise_row_count(inventory.release_manifest),
        synthetic_disclaimer=selected_note,
        associated_paper_title=ASSOCIATED_PAPER_TITLE,
        associated_paper_authors=ASSOCIATED_PAPER_AUTHORS,
        associated_paper_link=ASSOCIATED_PAPER_LINK,
        associated_paper_status=ASSOCIATED_PAPER_STATUS,
    ).strip() + "\n"


def render_publication_readme(inventory: ReleaseInventory) -> str:
    lines = [
        f"# {manifest_dataset_name(inventory.release_manifest)} Publication Bundle",
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
    # Publication bundles are intended to be shareable as-is, so they deliberately avoid
    # machine-local absolute paths. They describe release artifacts using release-relative paths.
    return {
        "dataset_name": manifest_dataset_name(inventory.release_manifest),
        "version": inventory.release_manifest.get("version", "unknown"),
        "release_type": inventory.release_manifest.get("release_type", "unknown"),
        "source_release_name": inventory.release_dir.name,
        "total_files_in_release_directory": inventory.total_files,
        "total_bytes_in_release_directory": inventory.total_bytes,
        "release_artifact_paths": dict(PUBLIC_RELEASE_ARTIFACT_RELATIVE_PATHS),
        "has_candidate_rows": inventory.has_candidate_rows,
        "has_decision_view": inventory.has_decision_view,
        "has_pairwise_view": inventory.has_pairwise_view,
        "has_pairwise_sample": inventory.has_pairwise_sample,
        "intended_huggingface_repo_id": "TODO/replace-with-dataset-repo-id",
        "intended_zenodo_deposition_id": "TODO",
        "intended_github_tag": "TODO",
        "publication_status": "draft_local",
        "bundle_directory_name": Path(bundle_dir).resolve().name,
    }


def write_json(path: str | Path, payload: dict[str, object]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_publication(path: Path) -> str:
    return _hash_file(path, "sha256")


def md5_file_publication(path: Path) -> str:
    return _hash_file(path, "md5")


def load_zenodo_metadata(path: str | Path) -> dict[str, object]:
    metadata_path = Path(path)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Zenodo metadata payload must be a JSON object.")
    validate_zenodo_v0_2_metadata(payload)
    return payload


def validate_zenodo_v0_2_metadata(payload: dict[str, object]) -> None:
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Zenodo metadata payload must contain a metadata object.")

    required_text = {
        "title": "LAFC-Evict: Learning-Augmented Cache Eviction Dataset",
        "upload_type": "dataset",
        "version": "v0.2",
        "license": "cc0-1.0",
        "access_right": "open",
        "language": "eng",
    }
    for key, expected in required_text.items():
        if metadata.get(key) != expected:
            raise ValueError(f"Zenodo metadata {key!r} must be {expected!r}.")

    creators = metadata.get("creators")
    if not isinstance(creators, list) or not creators:
        raise ValueError("Zenodo metadata must include at least one creator.")
    first_creator = creators[0]
    if not isinstance(first_creator, dict):
        raise ValueError("Zenodo metadata creator entries must be objects.")
    if first_creator.get("name") != "Vahidi, Soroush":
        raise ValueError("Zenodo metadata creator must be Vahidi, Soroush.")
    if first_creator.get("affiliation") != "New Jersey Institute of Technology":
        raise ValueError("Zenodo metadata creator affiliation must be New Jersey Institute of Technology.")

    description = str(metadata.get("description", ""))
    if "Wikimedia" not in description or "CC0" not in description or "raw page titles" not in description:
        raise ValueError("Zenodo metadata description must include Wiki2018 attribution and raw-title caveat.")

    keywords = metadata.get("keywords")
    if not isinstance(keywords, list) or len(keywords) < 5:
        raise ValueError("Zenodo metadata must include a non-trivial keyword list.")

    related = metadata.get("related_identifiers")
    if not isinstance(related, list):
        raise ValueError("Zenodo metadata related_identifiers must be a list.")
    expected_relations = {
        "https://huggingface.co/datasets/SoroushVahidi/lafc-evict": "isIdenticalTo",
        "https://github.com/SoroushVahidi/Augmented-caching": "isDocumentedBy",
    }
    seen: dict[str, str] = {}
    for item in related:
        if isinstance(item, dict):
            seen[str(item.get("identifier", ""))] = str(item.get("relation", ""))
    for identifier, relation in expected_relations.items():
        if seen.get(identifier) != relation:
            raise ValueError(f"Zenodo metadata must relate {identifier} as {relation}.")

    serialized = json.dumps(payload, sort_keys=True)
    forbidden = [
        "ZENODO_API_TOKEN",
        "ZENODO_ACCESS_TOKEN",
        "ZENODO_TOKEN",
        "Bearer ",
        "access_token=",
        "/home/",
        "/mmfs",
        "wulver",
    ]
    for marker in forbidden:
        if marker.lower() in serialized.lower():
            raise ValueError(f"Zenodo metadata contains forbidden marker: {marker}")


def load_zenodo_file_manifest(path: str | Path) -> ZenodoFileManifest:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Zenodo file manifest must be a JSON object.")
    files_payload = payload.get("files")
    if not isinstance(files_payload, list):
        raise ValueError("Zenodo file manifest must contain a files list.")
    files: list[ZenodoManifestFile] = []
    for item in files_payload:
        if not isinstance(item, dict):
            raise ValueError("Zenodo file manifest entries must be objects.")
        files.append(
            ZenodoManifestFile(
                path=str(item["path"]),
                bytes=int(item["bytes"]),
                sha256=str(item["sha256"]),
                md5=str(item["md5"]),
                role=str(item["role"]),
            )
        )
    manifest = ZenodoFileManifest(
        manifest_version=str(payload.get("manifest_version", "")),
        dataset=str(payload.get("dataset", "")),
        version=str(payload.get("version", "")),
        release_root_name=str(payload.get("release_root_name", "")),
        expected_file_count=int(payload.get("expected_file_count", -1)),
        expected_total_bytes=int(payload.get("expected_total_bytes", -1)),
        files=tuple(files),
    )
    validate_zenodo_file_manifest_structure(manifest)
    return manifest


def validate_zenodo_file_manifest_structure(manifest: ZenodoFileManifest) -> None:
    if manifest.manifest_version != "zenodo-file-manifest-v1":
        raise ValueError("Unsupported Zenodo file manifest version.")
    if manifest.dataset != "lafc-evict":
        raise ValueError("Zenodo file manifest dataset must be lafc-evict.")
    if manifest.version != "v0.2":
        raise ValueError("Zenodo file manifest version must be v0.2.")
    if manifest.release_root_name != "lafc-evict-v0.2-preview":
        raise ValueError("Zenodo file manifest release root must be lafc-evict-v0.2-preview.")
    if manifest.expected_file_count != 15:
        raise ValueError("Zenodo v0.2 manifest must contain exactly 15 files.")
    if len(manifest.files) != manifest.expected_file_count:
        raise ValueError("Zenodo file manifest file count does not match expected_file_count.")
    if len({entry.path for entry in manifest.files}) != len(manifest.files):
        raise ValueError("Zenodo file manifest contains duplicate paths.")
    if sum(entry.bytes for entry in manifest.files) != manifest.expected_total_bytes:
        raise ValueError("Zenodo file manifest byte total does not match expected_total_bytes.")
    for entry in manifest.files:
        if entry.path.startswith("/") or ".." in Path(entry.path).parts:
            raise ValueError(f"Unsafe Zenodo manifest path: {entry.path}")
        if not re.fullmatch(r"[0-9a-f]{64}", entry.sha256):
            raise ValueError(f"Invalid SHA-256 for {entry.path}")
        if not re.fullmatch(r"[0-9a-f]{32}", entry.md5):
            raise ValueError(f"Invalid MD5 for {entry.path}")


def validate_zenodo_v0_2_release_package(
    *,
    release_dir: str | Path,
    metadata_path: str | Path,
    manifest_path: str | Path,
) -> ZenodoDraftPlan:
    release_path = Path(release_dir).resolve()
    metadata_file = Path(metadata_path).resolve()
    manifest_file = Path(manifest_path).resolve()
    metadata = load_zenodo_metadata(metadata_file)
    manifest = load_zenodo_file_manifest(manifest_file)

    actual_files = tuple(sorted(path.relative_to(release_path).as_posix() for path in release_path.rglob("*") if path.is_file()))
    expected_files = tuple(entry.path for entry in manifest.files)
    if actual_files != expected_files:
        raise ValueError(
            "Release file inventory does not match Zenodo manifest. "
            f"Expected {len(expected_files)} files, found {len(actual_files)} files."
        )

    for entry in manifest.files:
        path = release_path / entry.path
        if not path.exists():
            raise FileNotFoundError(f"Missing Zenodo upload file: {entry.path}")
        size = path.stat().st_size
        if size != entry.bytes:
            raise ValueError(f"Size mismatch for {entry.path}: {size} vs {entry.bytes}")
        sha256 = sha256_file_publication(path)
        if sha256 != entry.sha256:
            raise ValueError(f"SHA-256 mismatch for {entry.path}: {sha256} vs {entry.sha256}")
        md5 = md5_file_publication(path)
        if md5 != entry.md5:
            raise ValueError(f"MD5 mismatch for {entry.path}: {md5} vs {entry.md5}")

    release_manifest = json.loads((release_path / "metadata" / "release_manifest.json").read_text(encoding="utf-8"))
    if release_manifest.get("dataset_name") != "lafc-evict":
        raise ValueError("Release manifest dataset_name must be lafc-evict.")
    if release_manifest.get("version") != "0.2-preview":
        raise ValueError("Release manifest version must be 0.2-preview.")
    if release_manifest.get("included_families") != ["wiki2018"]:
        raise ValueError("Release manifest must include only wiki2018.")

    security_scan = json.loads((release_path / "metadata" / "security_scan.json").read_text(encoding="utf-8"))
    if security_scan.get("passed") is not True or security_scan.get("findings") not in ([], ()):
        raise ValueError("Release security scan must pass with no findings.")

    readme = (release_path / "README.md").read_text(encoding="utf-8")
    dataset_card = (release_path / "dataset_card.md").read_text(encoding="utf-8")
    if 'license: "cc0-1.0"' not in readme:
        raise ValueError("Release README must declare Hugging Face license metadata as cc0-1.0.")
    if "Wikimedia pageview data is made available by the Wikimedia Foundation" not in readme + dataset_card:
        raise ValueError("Wiki2018 attribution text is missing from release documentation.")

    source_manifest = json.loads((release_path / "metadata" / "sampling_manifest.json").read_text(encoding="utf-8"))
    source_entries = source_manifest.get("source_entries", [])
    if not isinstance(source_entries, list) or not source_entries:
        raise ValueError("Sampling manifest must contain source_entries.")
    for entry in source_entries:
        if not isinstance(entry, dict):
            raise ValueError("Sampling manifest source entry must be an object.")
        rel_path = str(entry.get("source_relpath", ""))
        if rel_path.startswith("/") or "/wiki2018_pageviews_en_50k__" not in f"/{rel_path}":
            raise ValueError(f"Unexpected v0.2 source_relpath: {rel_path}")

    from lafc_evict_dataset.preview import validate_preview_release

    preview_errors = validate_preview_release(release_path)
    if preview_errors:
        raise ValueError("Preview release validation failed: " + "; ".join(preview_errors))

    return ZenodoDraftPlan(
        target="production",
        metadata_path=metadata_file,
        manifest_path=manifest_file,
        release_dir=release_path,
        metadata=metadata,
        file_manifest=manifest,
        operations=(
            "POST /api/deposit/depositions",
            "PUT /api/deposit/depositions/{id}",
            "PUT {bucket_url}/{relative_path} for each manifest file",
            "GET /api/deposit/depositions/{id}",
        ),
    )


def expected_hf_remote_paths(inventory: ReleaseInventory) -> tuple[str, ...]:
    paths = [
        "README.md",
        "metadata/release_manifest.json",
        "metadata/checksums.sha256",
        "metadata/validation_report.md",
    ]
    manifest_data_files = inventory.release_manifest.get("data_files", [])
    if isinstance(manifest_data_files, list) and manifest_data_files:
        paths.extend(str(path) for path in manifest_data_files)
    else:
        paths.extend(["data/candidate_rows/", "data/decision_view/"])
        if inventory.has_pairwise_view:
            paths.append("data/pairwise_view/")
        elif inventory.has_pairwise_sample:
            paths.append("data/pairwise_sample/")
    return tuple(paths)


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
    return bool(zenodo_api_token())


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
    files = list(safe_zenodo_bundle_filenames(bundle_dir))
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


def plan_zenodo_v0_2_draft(
    *,
    metadata_path: str | Path,
    release_dir: str | Path,
    manifest_path: str | Path,
    production: bool = True,
) -> ZenodoDraftPlan:
    plan = validate_zenodo_v0_2_release_package(
        release_dir=release_dir,
        metadata_path=metadata_path,
        manifest_path=manifest_path,
    )
    return ZenodoDraftPlan(
        target="production" if production else "sandbox",
        metadata_path=plan.metadata_path,
        manifest_path=plan.manifest_path,
        release_dir=plan.release_dir,
        metadata=plan.metadata,
        file_manifest=plan.file_manifest,
        operations=plan.operations,
    )


def render_zenodo_v0_2_dry_run(plan: ZenodoDraftPlan) -> dict[str, object]:
    metadata = plan.metadata["metadata"] if isinstance(plan.metadata.get("metadata"), dict) else {}
    return {
        "mode": "dry_run",
        "target": plan.target,
        "metadata": {
            "title": metadata.get("title"),
            "upload_type": metadata.get("upload_type"),
            "version": metadata.get("version"),
            "license": metadata.get("license"),
            "access_right": metadata.get("access_right"),
            "creators": metadata.get("creators"),
            "related_identifiers": metadata.get("related_identifiers"),
        },
        "manifest": {
            "path": str(plan.manifest_path),
            "release_dir": str(plan.release_dir),
            "file_count": plan.file_manifest.expected_file_count,
            "total_bytes": plan.file_manifest.expected_total_bytes,
            "files": [
                {
                    "path": entry.path,
                    "bytes": entry.bytes,
                    "sha256": entry.sha256,
                    "md5": entry.md5,
                    "role": entry.role,
                }
                for entry in plan.file_manifest.files
            ],
        },
        "would_run": list(plan.operations),
        "safety": {
            "no_deposition_created": True,
            "no_files_uploaded": True,
            "no_doi_published": True,
            "no_quota_allocated": True,
        },
        "explicit_statement": [
            "NO DEPOSITION CREATED",
            "NO FILES UPLOADED",
            "NO DOI PUBLISHED",
            "NO QUOTA ALLOCATED",
        ],
    }


def zenodo_api_token(*, sandbox: bool | None = None) -> str | None:
    if sandbox is True:
        sandbox_token = os.environ.get("ZENODO_SANDBOX_TOKEN")
        if sandbox_token:
            return sandbox_token
    api_token = os.environ.get("ZENODO_API_TOKEN")
    if api_token:
        return api_token
    access_token = os.environ.get("ZENODO_ACCESS_TOKEN")
    if access_token:
        return access_token
    token = os.environ.get("ZENODO_TOKEN")
    if token:
        return token
    if sandbox is not False:
        sandbox_token = os.environ.get("ZENODO_SANDBOX_TOKEN")
        if sandbox_token:
            return sandbox_token
    return None


def zenodo_base_url(*, sandbox: bool) -> str:
    return ZENODO_SANDBOX_BASE_URL if sandbox else ZENODO_PRODUCTION_BASE_URL


def safe_zenodo_bundle_filenames(bundle_dir: Path) -> tuple[str, ...]:
    return tuple(name for name in ZENODO_SAFE_BUNDLE_FILENAMES if (bundle_dir / name).exists())


def _sanitize_sensitive_text(text: str, *, token: str | None) -> str:
    sanitized = text
    if token:
        sanitized = sanitized.replace(token, "[REDACTED_TOKEN]")
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED_TOKEN]", sanitized)
    sanitized = re.sub(r"(access_token=)[^&\s]+", r"\1[REDACTED_TOKEN]", sanitized)
    return sanitized


def _safe_response_body(response: ResponseLike, *, token: str | None) -> str:
    try:
        body = json.dumps(response.json(), sort_keys=True)
    except Exception:
        body = response.text.strip()
    body = _sanitize_sensitive_text(body, token=token)
    return body[:2000]


def _raise_zenodo_error(action: str, response: ResponseLike, *, token: str | None) -> None:
    raise RuntimeError(
        f"{action} failed with status {response.status_code}: {_safe_response_body(response, token=token)}"
    )


def _request_json(
    session: SessionLike,
    method: str,
    url: str,
    *,
    token: str,
    json_payload: dict[str, object] | None = None,
    data: Any = None,
) -> dict[str, Any]:
    request = getattr(session, method)
    headers = {"Authorization": f"Bearer {token}"}
    kwargs: dict[str, Any] = {"headers": headers, "timeout": 30}
    if json_payload is not None:
        kwargs["json"] = json_payload
    if data is not None:
        kwargs["data"] = data
    response = request(url, **kwargs)
    if response.status_code >= 400:
        _raise_zenodo_error(f"{method.upper()} {url}", response, token=token)
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{method.upper()} {url} returned a non-object JSON response.")
    return payload


def execute_zenodo_deposit(
    bundle_dir: Path,
    *,
    sandbox: bool = True,
    include_release_files: bool = False,
    release_dir: Path | None = None,
    session: SessionLike | None = None,
) -> ZenodoExecutionResult:
    if session is None:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("Execute mode requires the optional 'requests' dependency.") from exc

        session = requests.Session()

    token = zenodo_api_token(sandbox=sandbox)
    if not token:
        raise ValueError("Execute mode requires a configured Zenodo token environment variable.")

    bundle_dir = bundle_dir.resolve()
    metadata_path = bundle_dir / "zenodo_metadata.json"
    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    base_url = zenodo_base_url(sandbox=sandbox)

    created = _request_json(
        session,
        "post",
        f"{base_url}/api/deposit/depositions",
        token=token,
        json_payload={},
    )

    deposition_id = int(created["id"])
    latest_draft_url = str(created.get("links", {}).get("latest_draft", f"{base_url}/api/deposit/depositions/{deposition_id}"))
    updated = _request_json(
        session,
        "put",
        latest_draft_url,
        token=token,
        json_payload=metadata_payload,
    )

    bucket_url = str(updated.get("links", {}).get("bucket") or created.get("links", {}).get("bucket", ""))
    if not bucket_url:
        raise RuntimeError("Zenodo deposition response did not include a bucket upload URL.")

    uploaded_filenames: list[str] = []
    for relative_name in safe_zenodo_bundle_filenames(bundle_dir):
        file_path = bundle_dir / relative_name
        with file_path.open("rb") as handle:
            _request_json(
                session,
                "put",
                f"{bucket_url}/{file_path.name}",
                token=token,
                data=handle,
            )
        uploaded_filenames.append(relative_name)

    if include_release_files and release_dir is not None:
        for path in sorted(release_dir.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(release_dir).as_posix()
            with path.open("rb") as handle:
                _request_json(
                    session,
                    "put",
                    f"{bucket_url}/{relative_path}",
                    token=token,
                    data=handle,
                )
            uploaded_filenames.append(f"release::{relative_path}")

    verified = _request_json(session, "get", latest_draft_url, token=token)
    verified_metadata = verified.get("metadata", {})
    links_payload = verified.get("links", {})
    safe_links = {
        key: str(value)
        for key, value in links_payload.items()
        if key in {"self", "html", "latest_draft", "latest_draft_html"}
    }
    prereserved_doi = None
    if isinstance(verified_metadata, dict):
        prereserve = verified_metadata.get("prereserve_doi", {})
        if isinstance(prereserve, dict):
            prereserved_doi = str(prereserve.get("doi")) if prereserve.get("doi") else None

    return ZenodoExecutionResult(
        target="sandbox" if sandbox else "production",
        deposition_id=int(verified.get("id", deposition_id)),
        concept_record_id=str(verified.get("conceptrecid")) if verified.get("conceptrecid") is not None else None,
        metadata_title=str(verified_metadata.get("title", "")) if isinstance(verified_metadata, dict) else "",
        uploaded_filenames=tuple(uploaded_filenames),
        links=safe_links,
        doi=str(verified.get("doi")) if verified.get("doi") else None,
        prereserved_doi=prereserved_doi,
        state=str(verified.get("state")) if verified.get("state") is not None else None,
        submitted=bool(verified.get("submitted")) if verified.get("submitted") is not None else None,
    )


def _zenodo_file_payload(file_payload: dict[str, object]) -> tuple[str | None, int | None, str | None]:
    filename = file_payload.get("filename") or file_payload.get("key")
    size = file_payload.get("filesize") or file_payload.get("size")
    checksum = file_payload.get("checksum")
    return (
        str(filename) if filename is not None else None,
        int(size) if size is not None else None,
        str(checksum) if checksum is not None else None,
    )


def zenodo_remote_filename(path: str) -> str:
    """Zenodo deposition buckets expose a flat file namespace."""
    return Path(path).name


def verify_zenodo_uploaded_draft(
    *,
    draft_payload: dict[str, object],
    file_manifest: ZenodoFileManifest,
    metadata: dict[str, object],
) -> None:
    if draft_payload.get("submitted") is not False:
        raise ValueError("Zenodo draft verification expected submitted=false.")
    state = draft_payload.get("state")
    if state not in {"unsubmitted", "inprogress"}:
        raise ValueError(f"Zenodo draft has unexpected state: {state}")
    if draft_payload.get("doi"):
        raise ValueError("Zenodo draft unexpectedly has a registered DOI.")

    verified_metadata = draft_payload.get("metadata")
    expected_metadata = metadata.get("metadata")
    if not isinstance(verified_metadata, dict) or not isinstance(expected_metadata, dict):
        raise ValueError("Zenodo draft metadata response is missing metadata objects.")
    for field in ["title", "upload_type", "version", "license", "access_right"]:
        observed_value = verified_metadata.get(field)
        expected_value = expected_metadata.get(field)
        if field == "license" and {observed_value, expected_value} <= {"cc-zero", "cc0-1.0"}:
            continue
        if observed_value != expected_value:
            raise ValueError(f"Zenodo draft metadata mismatch for {field}.")

    files_payload = draft_payload.get("files")
    if not isinstance(files_payload, list):
        raise ValueError("Zenodo draft response must include a files list.")
    if len(files_payload) != file_manifest.expected_file_count:
        raise ValueError(
            f"Zenodo draft file count mismatch: {len(files_payload)} vs {file_manifest.expected_file_count}"
        )

    expected = {zenodo_remote_filename(entry.path): entry for entry in file_manifest.files}
    if len(expected) != len(file_manifest.files):
        raise ValueError("Zenodo manifest contains duplicate remote basenames.")
    observed: dict[str, tuple[int | None, str | None]] = {}
    for file_payload in files_payload:
        if not isinstance(file_payload, dict):
            raise ValueError("Zenodo draft file entries must be objects.")
        filename, size, checksum = _zenodo_file_payload(file_payload)
        if filename is None:
            raise ValueError("Zenodo draft file entry is missing filename/key.")
        observed[filename] = (size, checksum)

    if set(observed) != set(expected):
        raise ValueError("Zenodo draft uploaded filenames do not match the manifest exactly.")
    for remote_name, entry in expected.items():
        size, checksum = observed[remote_name]
        if size != entry.bytes:
            raise ValueError(f"Zenodo draft size mismatch for {entry.path}: {size} vs {entry.bytes}")
        if checksum:
            normalized = checksum.lower()
            if normalized.startswith("md5:"):
                normalized = normalized.split(":", 1)[1]
            if normalized != entry.md5 and normalized != entry.sha256:
                raise ValueError(f"Zenodo draft checksum mismatch for {entry.path}: {checksum}")


def execute_zenodo_v0_2_draft(
    *,
    metadata_path: str | Path,
    release_dir: str | Path,
    manifest_path: str | Path,
    production: bool = True,
    deposition_id: int | None = None,
    session: SessionLike | None = None,
) -> ZenodoDraftExecutionResult:
    if session is None:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("Draft creation requires the optional 'requests' dependency.") from exc

        session = requests.Session()

    token = zenodo_api_token(sandbox=not production)
    if not token:
        raise ValueError("Draft creation requires ZENODO_API_TOKEN, ZENODO_ACCESS_TOKEN, ZENODO_TOKEN, or ZENODO_SANDBOX_TOKEN.")

    plan = plan_zenodo_v0_2_draft(
        metadata_path=metadata_path,
        release_dir=release_dir,
        manifest_path=manifest_path,
        production=production,
    )
    base_url = zenodo_base_url(sandbox=not production)

    created: dict[str, Any]
    if deposition_id is None:
        created = _request_json(
            session,
            "post",
            f"{base_url}/api/deposit/depositions",
            token=token,
            json_payload={},
        )
        deposition_id = int(created["id"])
    else:
        created = _request_json(
            session,
            "get",
            f"{base_url}/api/deposit/depositions/{deposition_id}",
            token=token,
        )
        if created.get("submitted") is not False or created.get("state") not in {"unsubmitted", "inprogress"}:
            raise ValueError("Existing Zenodo deposition is not an unpublished editable draft.")
    latest_draft_url = str(created.get("links", {}).get("latest_draft", f"{base_url}/api/deposit/depositions/{deposition_id}"))
    updated = _request_json(
        session,
        "put",
        latest_draft_url,
        token=token,
        json_payload=plan.metadata,
    )

    bucket_url = str(updated.get("links", {}).get("bucket") or created.get("links", {}).get("bucket", ""))
    if not bucket_url:
        raise RuntimeError("Zenodo deposition response did not include a bucket upload URL.")

    existing_payload = _request_json(session, "get", latest_draft_url, token=token)
    existing_files = existing_payload.get("files", [])
    existing_by_name: dict[str, tuple[int | None, str | None]] = {}
    if isinstance(existing_files, list):
        for file_payload in existing_files:
            if isinstance(file_payload, dict):
                filename, size, checksum = _zenodo_file_payload(file_payload)
                if filename is not None:
                    existing_by_name[filename] = (size, checksum)

    expected_remote_names = {zenodo_remote_filename(entry.path) for entry in plan.file_manifest.files}
    unexpected_existing = set(existing_by_name) - expected_remote_names
    if unexpected_existing:
        raise ValueError(f"Existing Zenodo draft contains unexpected files: {sorted(unexpected_existing)}")

    uploaded_filenames: list[str] = []
    for entry in plan.file_manifest.files:
        path = plan.release_dir / entry.path
        remote_name = zenodo_remote_filename(entry.path)
        existing = existing_by_name.get(remote_name)
        if existing is not None:
            existing_size, existing_checksum = existing
            normalized_checksum = (existing_checksum or "").lower().removeprefix("md5:")
            if existing_size != entry.bytes or normalized_checksum not in {entry.md5, entry.sha256}:
                raise ValueError(f"Existing Zenodo draft file conflicts with manifest: {entry.path}")
            uploaded_filenames.append(entry.path)
            continue
        with path.open("rb") as handle:
            _request_json(
                session,
                "put",
                f"{bucket_url}/{remote_name}",
                token=token,
                data=handle,
            )
        uploaded_filenames.append(entry.path)

    verified = _request_json(session, "get", latest_draft_url, token=token)
    verify_zenodo_uploaded_draft(
        draft_payload=verified,
        file_manifest=plan.file_manifest,
        metadata=plan.metadata,
    )

    verified_metadata = verified.get("metadata", {})
    links_payload = verified.get("links", {})
    safe_links = {
        key: str(value)
        for key, value in links_payload.items()
        if key in {"self", "html", "latest_draft", "latest_draft_html"}
    }
    prereserved_doi = None
    if isinstance(verified_metadata, dict):
        prereserve = verified_metadata.get("prereserve_doi", {})
        if isinstance(prereserve, dict):
            prereserved_doi = str(prereserve.get("doi")) if prereserve.get("doi") else None

    return ZenodoDraftExecutionResult(
        target=plan.target,
        deposition_id=int(verified.get("id", deposition_id)),
        concept_record_id=str(verified.get("conceptrecid")) if verified.get("conceptrecid") is not None else None,
        metadata_title=str(verified_metadata.get("title", "")) if isinstance(verified_metadata, dict) else "",
        uploaded_filenames=tuple(uploaded_filenames),
        links=safe_links,
        doi=str(verified.get("doi")) if verified.get("doi") else None,
        prereserved_doi=prereserved_doi,
        state=str(verified.get("state")) if verified.get("state") is not None else None,
        submitted=bool(verified.get("submitted")) if verified.get("submitted") is not None else None,
        total_bytes=plan.file_manifest.expected_total_bytes,
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
