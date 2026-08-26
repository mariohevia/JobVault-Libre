import os
import sys
import re
import json
import yaml
from importlib import resources
from pathlib import Path
from datetime import date
from typing import Any, Never

from myapp.exceptions import ConfigurationFormatError, ConfigurationMissingKeyError

# TODO: Use this in all config variables because the config should never miss a
# key in the code, otherwise something went wrong.
class ConfigDict(dict):
    """Dictionary that raises AppError with troubleshooting steps on missing keys."""

    def _raise_missing(self, key: str) -> Never:
        raise ConfigurationMissingKeyError(
            message=f"Missing configuration key: '{key}' in ConfigDict"
            )

    def __missing__(self, key: str) -> Never:
        self._raise_missing(key)

    def get(self, key, default=None):
        if key not in self:
            self._raise_missing(key)
        return super().get(key)


class JobDict(dict):
    """Dictionary that raises AppError with troubleshooting steps on missing keys."""

    id: int
    company: str
    position: str
    status: str
    company_website: str | None
    location: str | None
    source: str | None
    job_type: str | None
    date_applied: str | None
    contact_name: str | None
    contact_email: str | None
    salary_range: str | None
    work_arrangement: str | None
    office_days: int | None
    job_url: str | None
    job_description: str | None
    notes: str | None
    cv_pdf: bytes | None
    cv_text: str | None
    cover_letter_pdf: bytes | None
    cover_letter_text: str | None
    last_update: str

    def _raise_missing(self, key: str) -> Never:
        raise ConfigurationMissingKeyError(
            message=f"Missing configuration key: '{key}' in JobDict"
            )

    def __missing__(self, key: str) -> Never:
        self._raise_missing(key)

    def get(self, key: str, default: None = None) -> Never:
        if key not in self:
            self._raise_missing(key)
        return super().get(key)


class NewJobDict(dict):
    """Dictionary that raises AppError with troubleshooting steps on missing keys."""

    company: str
    position: str
    status: str
    company_website: str | None
    location: str | None
    source: str | None
    job_type: str | None
    date_applied: str | None
    contact_name: str | None
    contact_email: str | None
    salary_range: str | None
    work_arrangement: str | None
    office_days: int | None
    job_url: str | None
    job_description: str | None
    notes: str | None
    cv_pdf: bytes | None
    cv_text: str | None
    cover_letter_pdf: bytes | None
    cover_letter_text: str | None

    def _raise_missing(self, key: str) -> Never:
        raise ConfigurationMissingKeyError(
            message=f"Missing configuration key: '{key}' in JobDict"
            )

    def __missing__(self, key: str) -> Never:
        self._raise_missing(key)

    def get(self, key: str, default: None = None) -> Never:
        if key not in self:
            self._raise_missing(key)
        return super().get(key)


def today_year_month() -> tuple[int, int]:
    d = date.today()
    return d.year, d.month

def _safe_slug(value: str) -> str:
    # filesystem-safe: letters/numbers/_/-
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9_-]", "", value)
    return value or "default"

def get_app_data_dir(app_name: str) -> Path:
    """
    Return an OS-appropriate per-user application data directory.
    The directory is created if it does not exist.
    """
    if sys.platform.startswith("win"):
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        # TODO: Consider separating data from cache and configurations into XDG_CONFIG_HOME and XDG_CACHE_HOME.
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    app_dir = base_dir / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_app_paths_for_user(app_name: str, user_id: str) -> dict[str, Path]:
    base = get_app_data_dir(app_name) 
    profiles_dir = base / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    pid = _safe_slug(str(user_id))
    profile_dir = profiles_dir / pid
    profile_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "base": base,
        "users": profiles_dir,
        "user": profile_dir,
        "db": profile_dir / "database.sqlite",
        "settings": profile_dir / "settings.json",
        "config": profile_dir / "config.json",
        "cache": profile_dir / "cache",
        "cvs": profile_dir / "cvs",
        }
    paths["cache"].mkdir(parents=True, exist_ok=True)
    paths["cvs"].mkdir(parents=True, exist_ok=True)
    return paths

def save_full_config(config_path: str, full_cfg: dict[str, Any]) -> None:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(full_cfg, f, indent=2, ensure_ascii=False)

def field_default_value(field_def: dict[str, Any]) -> Any:
    ftype = field_def.get("type")

    # default_value from YAML if present and non-empty
    if "default_value" in field_def:
        dv = field_def.get("default_value")
        if dv is not None and str(dv).strip() != "":
            return dv

    if ftype == "year_month":
        y, m = today_year_month()
        return {"year": y, "month": m}

    if ftype == "enum":
        opts = field_def.get("options") or []
        return opts[0] if isinstance(opts, list) and opts else ""

    if ftype in ("string", "multiline"):
        return ""

    if ftype == "number":
        return 0

    if ftype == "object":
        # build dict for nested fields
        out = {}
        for sub in (field_def.get("fields") or []):
            if isinstance(sub, dict) and sub.get("name"):
                out[sub["name"]] = field_default_value(sub)
        return out

    return ""

def create_empty_config(section_defs: list[dict] | None = None) -> dict:
    """
    Creates an empty config dict matching the structure expected by the app.
    
    :param section_defs: list of section definition dicts (from load_section_names_from_yaml).
                         If None, sections will be an empty dict.
    """
    sections = {}

    if section_defs:
        for section_def in section_defs:
            section_name = section_def.get("name")
            if not section_name:
                continue

            fields = [f for f in (section_def.get("fields") or []) if isinstance(f, dict) and f.get("name")]
            allow_multiple = bool(section_def.get("allow_multiple", False))

            # Build default item payload
            item_payload = {}
            if allow_multiple:
                item_payload["selected_default"] = True

            for fdef in fields:
                fname = fdef["name"]
                is_multi = bool(fdef.get("allow_multiple", False))
                base = field_default_value(fdef)
                item_payload[fname] = [base] if is_multi else base

            # Build field_visibility
            def build_field_visibility(fields):
                visibility = {}
                for fdef in fields:
                    fname = fdef["name"]
                    if fdef.get("type") == "object":
                        sub_vis = build_field_visibility(fdef.get("fields") or [])
                        sub_vis["_visible"] = True
                        visibility[fname] = sub_vis
                    else:
                        visibility[fname] = True
                return visibility

            sections[section_name] = {
                "enabled": True,
                "preselected": True,
                "items": [item_payload],
                "field_visibility": build_field_visibility(fields),
                }

    return {
        "cv_config": {
            "section_order": [s["name"] for s in (section_defs or []) if s.get("name")],
            "sections": sections,
            }
        }

def load_full_config(config_path: str) -> dict:
    if not config_path:
        raise RuntimeError("Configuration path not found")

    if not os.path.exists(config_path):
        section_defs = load_section_names_from_yaml()
        empty_config = create_empty_config(section_defs)
        save_full_config(config_path, empty_config)
        return empty_config
    
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)

        except json.JSONDecodeError as e:
            raise ConfigurationFormatError(
                f"Invalid JSON configuration file: {config_path}"
            ) from e

    if not isinstance(data, dict):
        raise ConfigurationFormatError("Invalid configuration file format")

    if "cv_config" not in data or not isinstance(data.get("cv_config"), dict):
        raise ConfigurationFormatError("Incorrect 'cv_config' format in configuration file")

    # TODO: Check that all sections have their configuration in a correct format
    if "sections" not in data.get("cv_config") or not isinstance(data["cv_config"].get("sections"), dict):
        raise ConfigurationFormatError("Incorrect 'sections' format in configuration file")

    return data

def load_cv_config(config_path: str) -> dict[str, Any]:
    cv_config = load_full_config(config_path).get("cv_config")

    return cv_config

def load_section_names_from_yaml() -> list[dict]:
    """
    Load the static section schema from myapp/resources/section_types.yml
    """
    try:
        with resources.files("myapp.resources").joinpath("section_types.yml").open(
            "r",
            encoding="utf-8",
        ) as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return []
    except Exception:
        # Fail gracefully if YAML is invalid
        return []

    sections = data.get("sections", []) or []
    if not isinstance(sections, list):
        return []
    return sections
    
def palette_color_to_rgba(c, a=100):
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a})"