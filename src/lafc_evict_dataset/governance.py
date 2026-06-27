from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import yaml

REQUIRED_REGISTRY_FIELDS: Final[tuple[str, ...]] = (
    "family",
    "source_name",
    "source_url",
    "upstream_license",
    "redistribution_status",
    "recommended_for_v0_1_open",
    "privacy_risk",
    "notes",
    "required_citation",
    "review_status",
)

REQUIRED_FAMILIES: Final[tuple[str, ...]] = (
    "twemcache",
    "metakv",
    "metacdn",
    "cloudphysics",
    "wiki2018",
    "citibike",
    "brightkite",
)

BLOCKED_STATUSES: Final[set[str]] = {"blocked", "blocked_pending_review"}


def load_source_family_registry(path: str | Path) -> list[dict[str, object]]:
    registry_path = Path(path)
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse registry YAML at {registry_path}: {exc}") from exc

    if not isinstance(payload, dict) or "families" not in payload:
        raise ValueError("Registry YAML must be a mapping with a top-level 'families' list.")
    families = payload["families"]
    if not isinstance(families, list):
        raise ValueError("Registry field 'families' must be a list.")

    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, entry in enumerate(families):
        if not isinstance(entry, dict):
            raise ValueError(f"Registry entry at index {index} must be a mapping.")
        missing = [field for field in REQUIRED_REGISTRY_FIELDS if field not in entry]
        if missing:
            raise ValueError(
                f"Registry entry at index {index} is missing required fields: {', '.join(missing)}"
            )
        family = str(entry["family"]).strip()
        if not family:
            raise ValueError(f"Registry entry at index {index} has an empty family name.")
        if family in seen:
            raise ValueError(f"Duplicate family entry in registry: {family}")
        seen.add(family)
        normalized.append({key: entry[key] for key in REQUIRED_REGISTRY_FIELDS})

    missing_families = [family for family in REQUIRED_FAMILIES if family not in seen]
    if missing_families:
        raise ValueError(
            "Registry is missing required families: " + ", ".join(missing_families)
        )
    return sorted(normalized, key=lambda item: str(item["family"]))


def select_release_families(
    registry: list[dict[str, object]],
    *,
    release_scope: str,
) -> dict[str, object]:
    if release_scope != "v0.1-open":
        raise ValueError(f"Unsupported release scope: {release_scope}")

    selected: list[str] = []
    excluded: list[dict[str, str]] = []
    for entry in sorted(registry, key=lambda item: str(item["family"])):
        family = str(entry["family"])
        redistribution_status = str(entry["redistribution_status"]).strip()
        recommended = bool(entry["recommended_for_v0_1_open"])
        if recommended and redistribution_status not in BLOCKED_STATUSES:
            selected.append(family)
            continue

        reasons: list[str] = []
        if not recommended:
            reasons.append("not recommended for v0.1-open")
        if redistribution_status in BLOCKED_STATUSES:
            reasons.append(f"redistribution_status={redistribution_status}")
        excluded.append(
            {
                "family": family,
                "reason": "; ".join(reasons) if reasons else "excluded by registry policy",
            }
        )

    return {
        "release_scope": release_scope,
        "selected_families": selected,
        "excluded_families": excluded,
        "warning": (
            "This selector output is a release-governance aid based on repository metadata. "
            "It is not legal advice."
        ),
    }


def write_selected_families_manifest(payload: dict[str, object], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
