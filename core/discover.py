from pathlib import Path

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")

def find_data_files(directory: str = ".") -> list[str]:
    """Return all CSV/Excel files in the given directory, sorted by name."""
    path = Path(directory)
    files = [
        str(f) for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)