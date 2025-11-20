import os
import sys
from typing import Optional

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

for path in (PROJECT_ROOT, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from recommender import (  # type: ignore  # pylint: disable=import-error
    DEFAULT_CSV_PATH,
    DEFAULT_PROCESSED_CSV_PATH,
    DEFAULT_PERSIST_DIR,
    DEFAULT_QUERY,
    DEFAULT_TOP_K,
    Recommender,
)
from data_loader import LoadData  # type: ignore  # pylint: disable=import-error

from utils.logger import get_logger

from .pipeline import AnimeRecommendationPipeline


class PipelineBuilder:
    """Fluent helper for configuring and instantiating the recommendation pipeline."""

    def __init__(self) -> None:
        self._logger = get_logger(self.__class__.__name__)
        self._query: str = DEFAULT_QUERY
        self._csv_path: str = DEFAULT_CSV_PATH
        self._processed_csv_path: Optional[str] = DEFAULT_PROCESSED_CSV_PATH
        self._persist_dir: str = DEFAULT_PERSIST_DIR
        self._top_k: int = DEFAULT_TOP_K
        self._rebuild_store: bool = False

    def with_query(self, query: str) -> "PipelineBuilder":
        if not query:
            raise ValueError("Query must be a non-empty string.")
        self._query = query
        return self

    def with_csv_path(self, csv_path: str) -> "PipelineBuilder":
        if not csv_path:
            raise ValueError("CSV path must be provided.")
        self._csv_path = csv_path
        return self

    def with_processed_csv_path(self, processed_csv_path: Optional[str]) -> "PipelineBuilder":
        self._processed_csv_path = processed_csv_path
        return self

    def with_persist_dir(self, persist_dir: str) -> "PipelineBuilder":
        if not persist_dir:
            raise ValueError("Persist directory must be provided.")
        self._persist_dir = persist_dir
        return self

    def with_top_k(self, top_k: int) -> "PipelineBuilder":
        if top_k <= 0:
            raise ValueError("Top_k must be a positive integer.")
        self._top_k = top_k
        return self

    def with_rebuild_store(self, rebuild: bool) -> "PipelineBuilder":
        self._rebuild_store = rebuild
        return self

    def build(self) -> AnimeRecommendationPipeline:
        """Create the configured :class:`AnimeRecommendationPipeline` instance."""
        csv_path = os.path.abspath(os.path.expanduser(self._csv_path))
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found at '{csv_path}'.")

        if self._processed_csv_path:
            processed_csv_path = os.path.abspath(os.path.expanduser(self._processed_csv_path))
        else:
            base, ext = os.path.splitext(csv_path)
            processed_csv_path = f"{base}_processed{ext or '.csv'}"

        persist_dir = os.path.abspath(os.path.expanduser(self._persist_dir))
        os.makedirs(os.path.dirname(processed_csv_path), exist_ok=True)
        os.makedirs(persist_dir, exist_ok=True)

        self._logger.info(
            "Building pipeline with csv='%s', processed='%s', persist_dir='%s', top_k=%s.",
            csv_path,
            processed_csv_path,
            persist_dir,
            self._top_k,
        )

        data_loader = LoadData(csv_file_path=csv_path, processed_csv_file_path=processed_csv_path)
        recommender = Recommender(
            csv_file_path=processed_csv_path,
            persist_dir=persist_dir,
            rebuild_store=self._rebuild_store,
        )

        return AnimeRecommendationPipeline(
            data_loader=data_loader,
            recommender=recommender,
            query=self._query,
            top_k=self._top_k,
        )

