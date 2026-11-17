"""Configuration: load `config/settings.yaml` and `.env` into a validated Settings object.

Parameter names and defaults follow System Specification §4.13. Unknown keys are an error.
"""

from __future__ import annotations

import os
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SECRET_NAMES = ("TIINGO_API_KEY", "FRED_API_KEY")


def find_repo_root(start: Path | None = None) -> Path:
    """Return the repository root (folder containing pyproject.toml). `ESW_ROOT` overrides."""
    env_root = os.environ.get("ESW_ROOT")
    if env_root:
        return Path(env_root).resolve()
    candidates = [start or Path.cwd(), Path(__file__).resolve()]
    for c in candidates:
        for p in [c, *c.parents]:
            if (p / "pyproject.toml").exists() and (p / "config").is_dir():
                return p
    raise FileNotFoundError("Could not locate the repository root (pyproject.toml + config/).")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PathsCfg(_Strict):
    config: str
    reference: str
    data: str
    raw: str
    manual_drop: str
    staged: str
    curated: str
    derived: str
    manifests: str
    runs: str
    models: str
    outputs: str
    reports: str
    logs: str
    records: str


class Params(_Strict):
    ABS_FLOOR_BPS: float = Field(gt=0)
    K_MULT: float = Field(gt=0)
    PERSIST_MIN: int = Field(ge=1)
    GAP_BRIDGE: int = Field(ge=0)
    HORIZON: int = Field(ge=1)
    BASE_WIN: int = Field(ge=1)
    BASE_MIN: int = Field(ge=1)
    SCALE_WIN: int = Field(ge=1)
    SCALE_MIN: int = Field(ge=1)
    SCALE_FLOOR_BPS: float = Field(gt=0)
    FREEZE_MAX: int = Field(ge=1)
    COOLDOWN: int = Field(ge=0)
    EMBARGO: int = Field(ge=0)
    SEC_ABS_BPS: float = Field(gt=0)
    SEC_RUN: int = Field(ge=1)
    SEBI_ABS_BPS: float = Field(gt=0)
    SEBI_RUN: int = Field(ge=1)
    LEAD_WINDOW: int = Field(ge=1)
    DEV_END: date
    LOCKBOX_START: date
    DATA_CUTOFF: date | None = None
    ALERT_BUDGET_HIGH: float = Field(gt=0)
    ALERT_BUDGET_WATCH: float = Field(gt=0)
    THR_WATCH: float | None = None
    THR_HIGH: float | None = None
    SEED: int
    BOOT_BLOCK: str
    BOOT_N: int = Field(ge=100)

    @field_validator("THR_WATCH", "THR_HIGH")
    @classmethod
    def _prob(cls, v: float | None) -> float | None:
        if v is not None and not 0 < v < 1:
            raise ValueError("thresholds must be probabilities in (0, 1)")
        return v

    @model_validator(mode="after")
    def _consistency(self) -> Params:
        if self.BASE_MIN > self.BASE_WIN or self.SCALE_MIN > self.SCALE_WIN:
            raise ValueError("minimum observations cannot exceed window length")
        if self.EMBARGO < self.HORIZON + self.PERSIST_MIN + self.GAP_BRIDGE + 1:
            raise ValueError("EMBARGO must be >= HORIZON + PERSIST_MIN + GAP_BRIDGE + 1 (System Spec §4.7)")
        if self.LOCKBOX_START <= self.DEV_END:
            raise ValueError("LOCKBOX_START must be after DEV_END")
        if self.BOOT_BLOCK != "month":
            raise ValueError("BOOT_BLOCK must be 'month' (System Spec §4.13)")
        if self.THR_WATCH is not None and self.THR_HIGH is not None and self.THR_WATCH >= self.THR_HIGH:
            raise ValueError("THR_WATCH must be below THR_HIGH")
        return self


class SensitivityGrid(_Strict):
    ABS_FLOOR_BPS: list[float]
    K_MULT: list[float]
    PERSIST_MIN: list[int]
    HORIZON: list[int]


class HttpCfg(_Strict):
    user_agent_env: str
    default_user_agent: str
    min_seconds_between_requests: float = Field(ge=0)
    max_retries: int = Field(ge=0)
    backoff_base_seconds: float = Field(ge=0)
    timeout_seconds: float = Field(gt=0)


class RuntimeCfg(_Strict):
    num_threads: int = Field(ge=1)


class Settings(_Strict):
    paths: PathsCfg
    params: Params
    sensitivity_grid: SensitivityGrid
    http: HttpCfg
    runtime: RuntimeCfg
    sources: dict[str, Any] = Field(default_factory=dict)

    # Not part of the YAML; filled by load_settings.
    root: Path | None = None

    def path(self, name: str) -> Path:
        """Absolute path for a key of `paths`."""
        rel = getattr(self.paths, name)
        assert self.root is not None
        return (self.root / rel).resolve()

    @property
    def user_agent(self) -> str:
        return os.environ.get(self.http.user_agent_env) or self.http.default_user_agent


def load_settings(path: Path | None = None, root: Path | None = None) -> Settings:
    """Load and validate settings. Also loads `.env` (without overriding existing env vars)."""
    root = root or find_repo_root()
    load_dotenv(root / ".env", override=False)
    path = path or root / "config" / "settings.yaml"
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    settings = Settings.model_validate(raw)
    settings.root = root
    return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings for the current repository."""
    return load_settings()


def secret_status() -> dict[str, bool]:
    """Which secrets are set (never their values)."""
    return {name: bool(os.environ.get(name)) for name in SECRET_NAMES}
