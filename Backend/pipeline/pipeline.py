import os
import sys
from typing import TYPE_CHECKING, List, Optional

from langchain_core.tools import tool

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

for path in (PROJECT_ROOT, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from data_loader import LoadData  # type: ignore  # pylint: disable=import-error
from recommender import (  # type: ignore  # pylint: disable=import-error
    DEFAULT_CSV_PATH,
    DEFAULT_PERSIST_DIR,
    DEFAULT_PROCESSED_CSV_PATH,
    DEFAULT_TOP_K,
    Recommender,
    _format_results,
)
from utils.logger import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from .builder import PipelineBuilder


class AnimeRecommendationPipeline:
    """High-level orchestration wrapper for the recommendation workflow."""

    def __init__(
        self,
        data_loader: LoadData,
        recommender: Recommender,
        query: str,
        top_k: int = 3,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        self.data_loader = data_loader
        self.recommender = recommender
        self.query = query
        self.top_k = top_k
        self.logger = get_logger(self.__class__.__name__)

        self._last_results: Optional[List] = None
        self._last_formatted: Optional[str] = None

    def run(self) -> str:
        """Execute the configured pipeline and return formatted recommendations."""
        self.logger.info("Executing recommendation pipeline for query='%s'.", self.query)
        processed_path = self.data_loader.process()
        self.logger.debug("Processed dataset available at '%s'.", processed_path)

        results = self.recommender.retrival(self.query, k=self.top_k)
        formatted = _format_results(results)

        self._last_results = results
        self._last_formatted = formatted

        self.logger.info("Pipeline completed with %s results.", len(results))
        return formatted

    @property
    def last_results(self) -> Optional[List]:
        """Return the raw results from the most recent run, if available."""
        return self._last_results

    @property
    def last_formatted(self) -> Optional[str]:
        """Return the last formatted output from the most recent run."""
        return self._last_formatted


@tool("run_anime_recommendations", return_direct=True)
def run_anime_recommendations_tool(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    LangChain-compatible tool that runs the anime recommendation pipeline.

    Parameters
    ----------
    query:
        Natural language description of the anime the user is looking for.
    top_k:
        Number of recommendations to return. Defaults to the project-wide default.

    Returns
    -------
    str
        Formatted recommendation list ready for presentation to the user.
    """

    if not query or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    try:
        top_k_value = int(top_k)
    except (TypeError, ValueError) as exc:
        raise ValueError("top_k must be an integer.") from exc

    if top_k_value <= 0:
        raise ValueError("top_k must be a positive integer.")

    from .builder import PipelineBuilder  # Local import to avoid circular dependency

    pipeline: "PipelineBuilder" = (
        PipelineBuilder()
        .with_query(query.strip())
        .with_top_k(top_k_value)
        .with_csv_path(DEFAULT_CSV_PATH)
        .with_processed_csv_path(DEFAULT_PROCESSED_CSV_PATH)
        .with_persist_dir(DEFAULT_PERSIST_DIR)
    )

    tool_logger = get_logger("AnimeRecommendationTool")
    tool_logger.info("Launching LangChain tool for query='%s' (top_k=%s).", query, top_k_value)

    recommendation_pipeline = pipeline.build()
    return recommendation_pipeline.run()