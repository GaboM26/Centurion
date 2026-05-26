"""Path helpers for Centurion."""

from pathlib import Path


def resolve_project_root(current_file: Path | None = None) -> Path:
    """Resolve the project root for local execution."""
    current_path = (current_file or Path(__file__)).resolve()

    for candidate in (current_path.parents[2], current_path.parents[1]):
        if (candidate / "src").exists():
            return candidate

    return current_path.parents[2]


PROJECT_ROOT = resolve_project_root()
