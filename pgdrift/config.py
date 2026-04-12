"""Configuration loader for pgdrift.

Handles loading and validating database connection profiles
from a YAML config file (default: pgdrift.yml).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

DEFAULT_CONFIG_PATH = Path("pgdrift.yml")


@dataclass
class DatabaseProfile:
    name: str
    host: str
    port: int
    dbname: str
    user: str
    password: Optional[str] = None

    def dsn(self) -> str:
        """Return a libpq-compatible connection string."""
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.dbname}",
            f"user={self.user}",
        ]
        if self.password:
            parts.append(f"password={self.password}")
        return " ".join(parts)


@dataclass
class Config:
    profiles: Dict[str, DatabaseProfile]

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> "Config":
        """Load config from a YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open() as fh:
            raw = yaml.safe_load(fh) or {}

        profiles_raw = raw.get("profiles", {})
        if not profiles_raw:
            raise ValueError("Config must define at least one profile under 'profiles'.")

        profiles: Dict[str, DatabaseProfile] = {}
        for name, cfg in profiles_raw.items():
            profiles[name] = DatabaseProfile(
                name=name,
                host=cfg.get("host", "localhost"),
                port=int(cfg.get("port", 5432)),
                dbname=cfg["dbname"],
                user=cfg.get("user", os.getenv("USER", "postgres")),
                password=cfg.get("password") or os.getenv("PGPASSWORD"),
            )

        return cls(profiles=profiles)

    def get_profile(self, name: str) -> DatabaseProfile:
        if name not in self.profiles:
            available = ", ".join(self.profiles.keys())
            raise KeyError(f"Profile '{name}' not found. Available: {available}")
        return self.profiles[name]
