import os
from typing import Optional

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


class LoadData:
    """Utility to clean and enrich the source anime CSV before indexing."""

    def __init__(self, csv_file_path: str, processed_csv_file_path: Optional[str] = None) -> None:
        self.csv_file_path = csv_file_path
        if processed_csv_file_path is None:
            base, ext = os.path.splitext(csv_file_path)
            processed_csv_file_path = f"{base}_processed{ext or '.csv'}"
        self.processed_csv_file_path = processed_csv_file_path

    def process(self) -> str:
        """Return the path to a processed CSV with a combined info column."""
        if not os.path.exists(self.csv_file_path):
            logger.error("CSV file not found at '%s'.", self.csv_file_path)
            raise FileNotFoundError(f"CSV file not found at '{self.csv_file_path}'.")

        logger.info("Loading anime data from '%s'.", self.csv_file_path)
        df = pd.read_csv(
            self.csv_file_path,
            encoding="utf-8",
            on_bad_lines="skip",
        )

        required_cols = {"Name", "Genres", "sypnopsis"}
        missing = required_cols - set(df.columns)
        if missing:
            missing_cols = ", ".join(sorted(missing))
            logger.error("Missing column(s) in CSV file: %s", missing_cols)
            raise ValueError(f"Missing column(s) in CSV file: {missing_cols}")

        df = df.dropna(subset=list(required_cols), how="any").fillna("")

        df["combined_info"] = (
            "Title: "
            + df["Name"].astype(str).str.strip()
            + " Overview: "
            + df["sypnopsis"].astype(str).str.strip()
            + " Genres: "
            + df["Genres"].astype(str).str.strip()
        )

        target_dir = os.path.dirname(self.processed_csv_file_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        df.to_csv(self.processed_csv_file_path, index=False, encoding="utf-8")
        logger.info(
            "Processed %s anime records into '%s'.",
            len(df),
            self.processed_csv_file_path,
        )
        return self.processed_csv_file_path