from pathlib import Path
import pandas as pd

def export_dataframe(df: pd.DataFrame, filepath: str) -> None:
    """Save a DataFrame to CSV or Excel, based on the filepath's extension."""
    path = Path(filepath)

    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        df.to_excel(path, index=False)
    else:
        raise ValueError(f"Unsupported export format: {path.suffix}")