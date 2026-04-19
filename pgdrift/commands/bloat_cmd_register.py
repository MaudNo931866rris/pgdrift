"""Entry point shim so register_all can import bloat_cmd cleanly."""
from pgdrift.commands.bloat_cmd import register  # noqa: F401
