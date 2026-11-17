"""Settings load and match System Specification §4.13 defaults."""

from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from esw.config import find_repo_root, load_settings

# System Specification §4.13 (defaults at documentation version 1.0).
EXPECTED_PARAMS = {
    "ABS_FLOOR_BPS": 200,
    "K_MULT": 3.0,
    "PERSIST_MIN": 3,
    "GAP_BRIDGE": 1,
    "HORIZON": 5,
    "BASE_WIN": 60,
    "BASE_MIN": 40,
    "SCALE_WIN": 250,
    "SCALE_MIN": 120,
    "SCALE_FLOOR_BPS": 5,
    "FREEZE_MAX": 60,
    "COOLDOWN": 5,
    "EMBARGO": 10,
    "SEC_ABS_BPS": 200,
    "SEC_RUN": 8,
    "SEBI_ABS_BPS": 100,
    "SEBI_RUN": 7,
    "LEAD_WINDOW": 5,
    "DEV_END": date(2019, 12, 31),
    "LOCKBOX_START": date(2020, 1, 1),
    "ALERT_BUDGET_HIGH": 1.0,
    "ALERT_BUDGET_WATCH": 1.0,
    "SEED": 20261117,
    "BOOT_BLOCK": "month",
    "BOOT_N": 2000,
}
# Set in later phases; may be null until then.
LATER_PARAMS = {"DATA_CUTOFF", "THR_WATCH", "THR_HIGH"}


@pytest.fixture(scope="module")
def settings():
    return load_settings()


def test_all_spec_parameters_present(settings):
    present = set(settings.params.model_dump())
    assert present == set(EXPECTED_PARAMS) | LATER_PARAMS


@pytest.mark.parametrize("name,expected", sorted(EXPECTED_PARAMS.items()))
def test_parameter_defaults(settings, name, expected):
    assert getattr(settings.params, name) == expected


def test_sensitivity_grid(settings):
    g = settings.sensitivity_grid
    assert g.ABS_FLOOR_BPS == [100, 200, 300]
    assert g.K_MULT == [2.5, 3.0, 4.0]
    assert g.PERSIST_MIN == [2, 3, 5]
    assert g.HORIZON == [1, 3, 5]


def test_paths_resolve_inside_repo(settings):
    root = find_repo_root()
    for name in ("raw", "curated", "runs", "manifests"):
        assert root in settings.path(name).parents


def _write_modified(tmp_path: Path, **overrides) -> Path:
    root = find_repo_root()
    raw = yaml.safe_load((root / "config" / "settings.yaml").read_text(encoding="utf-8"))
    for k, v in overrides.items():
        if k == "_extra":
            raw["unexpected_key"] = v
        else:
            raw["params"][k] = v
    p = tmp_path / "settings.yaml"
    p.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return p


@pytest.mark.parametrize(
    "override",
    [
        {"ABS_FLOOR_BPS": -1},
        {"EMBARGO": 3},
        {"THR_WATCH": 0.5, "THR_HIGH": 0.2},
        {"THR_HIGH": 1.5},
        {"LOCKBOX_START": "2019-06-01"},
        {"_extra": 1},
    ],
)
def test_invalid_settings_rejected(tmp_path, override):
    with pytest.raises(ValidationError):
        load_settings(path=_write_modified(tmp_path, **override))
