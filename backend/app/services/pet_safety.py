import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal


SafetyLevel = Literal["safe", "mild", "toxic"]
DATA_PATH = Path(__file__).parents[1] / "data" / "pet_toxicity.json"


@dataclass(frozen=True)
class PetSafetyInfo:
    species_pattern: str
    common_name: str
    cats: SafetyLevel
    dogs: SafetyLevel
    severity: SafetyLevel
    placement_tip: str
    note: str


def normalize_species(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


@lru_cache(maxsize=1)
def load_pet_safety_data() -> tuple[PetSafetyInfo, ...]:
    with DATA_PATH.open(encoding="utf-8") as data_file:
        records = json.load(data_file)
    return tuple(PetSafetyInfo(**record) for record in records)


def resolve_species(species: str) -> PetSafetyInfo | None:
    query = normalize_species(species)
    if not query:
        return None
    records = load_pet_safety_data()
    exact = [
        record
        for record in records
        if query
        in {
            normalize_species(record.species_pattern),
            normalize_species(record.common_name),
        }
    ]
    if exact:
        return exact[0]
    matches = [
        record
        for record in records
        if query in normalize_species(record.species_pattern)
        or normalize_species(record.species_pattern) in query
        or query in normalize_species(record.common_name)
        or normalize_species(record.common_name) in query
    ]
    return max(matches, key=lambda item: len(normalize_species(item.species_pattern))) if matches else None


def compose_placement_tip(severity: str, sunlight: str) -> str:
    light = sunlight.casefold()
    if severity == "toxic":
        location = "a bright spot" if "direct" in light else "its suitable light"
        return f"Keep in {location} above cat and dog height; a hanging planter is ideal."
    if severity == "mild":
        return "Place on a high shelf away from curious pets and clean up fallen leaves."
    return "Pet-safe placement; keep in the recommended light and discourage chewing."


def fields_for_species(species: str, sunlight: str) -> dict[str, object | None]:
    info = resolve_species(species)
    if info is None:
        return {
            "pet_safety": None,
            "pet_severity": None,
            "toxic_cats": None,
            "toxic_dogs": None,
            "placement_tip": None,
        }
    return {
        "pet_safety": info.severity,
        "pet_severity": info.severity,
        "toxic_cats": info.cats != "safe",
        "toxic_dogs": info.dogs != "safe",
        "placement_tip": compose_placement_tip(info.severity, sunlight),
    }
