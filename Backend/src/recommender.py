import os
import sys
from typing import List

from src.data_loader import LoadData
from utils.logger import get_logger
from src.vector_store import VectorStore

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))

DEFAULT_QUERY = "space bounty hunter adventure"
DEFAULT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "anime_with_synopsis.csv")
DEFAULT_PROCESSED_CSV_PATH = None  # computed automatically if left None
DEFAULT_PERSIST_DIR = os.path.join(PROJECT_ROOT, "VectorDataBase", "chromaDB")
DEFAULT_TOP_K = 3


class Recommender:
    def __init__(self, csv_file_path: str, persist_dir: str, rebuild_store: bool = False) -> None:
        self.persist_dir = persist_dir
        self.rebuild_store = rebuild_store
        self.vector_store = VectorStore(csv_path=csv_file_path, persist_dir=persist_dir)
        self.logger = get_logger(self.__class__.__name__)

    def retrival(self, query: str, k: int = 3):
        if k <= 0:
            raise ValueError("k must be a positive integer.")

        self.logger.info("Running retrieval for query='%s' with top_k=%s.", query, k)
        self.vector_store.Builder(force_rebuild=self.rebuild_store)
        # Avoid rebuilding repeatedly within the same process after the first call.
        self.rebuild_store = False

        store = self.vector_store.load_vector_store()
        results = store.similarity_search(query, k=k)
        self.logger.info("Retrieved %s candidate results.", len(results))
        return results


def _format_results(results: List) -> str:
    if not results:
        return "No matching anime found."

    formatted_chunks = []
    for idx, doc in enumerate(results, start=1):
        metadata = doc.metadata or {}
        title = metadata.get("Name") or metadata.get("title") or "Unknown Title"
        score = metadata.get("Score")
        genres = metadata.get("Genres")
        synopsis = doc.page_content.strip()

        chunk_lines = [f"{idx}. {title}"]

        if score:
            chunk_lines.append(f"   Score: {score}")

        if genres:
            chunk_lines.append(f"   Genres: {genres}")

        chunk_lines.append(f"   Synopsis: {synopsis}")
        formatted_chunks.append("\n".join(chunk_lines))

    return "\n\n".join(formatted_chunks)


def main() -> None:
    logger = get_logger(__name__)

    query = os.getenv("RECOMMENDER_QUERY", DEFAULT_QUERY)

    csv_path = os.getenv("RECOMMENDER_CSV_PATH", DEFAULT_CSV_PATH)
    csv_path = os.path.abspath(os.path.expanduser(csv_path))
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at '{csv_path}'.")

    logger.info("Starting recommendation run for query: %s", query)
    logger.info("Using raw CSV at '%s'.", csv_path)

    processed_csv_path = os.getenv("RECOMMENDER_PROCESSED_CSV_PATH", DEFAULT_PROCESSED_CSV_PATH or "")
    if processed_csv_path:
        processed_csv_path = os.path.abspath(os.path.expanduser(processed_csv_path))
    else:
        base, ext = os.path.splitext(csv_path)
        processed_csv_path = f"{base}_processed{ext or '.csv'}"

    data_loader = LoadData(csv_file_path=csv_path, processed_csv_file_path=processed_csv_path)
    processed_csv_path = data_loader.process()
    logger.info("Processed CSV available at '%s'.", processed_csv_path)

    persist_dir = os.getenv("RECOMMENDER_PERSIST_DIR", DEFAULT_PERSIST_DIR)
    persist_dir = os.path.abspath(os.path.expanduser(persist_dir))
    logger.info("Vector store persistence directory: '%s'.", persist_dir)

    sqlite_path = os.path.join(persist_dir, "chroma.sqlite3")
    index_dir = os.path.join(persist_dir, "index")
    vector_store_exists = os.path.exists(sqlite_path) or os.path.exists(index_dir)

    env_rebuild = os.getenv("RECOMMENDER_REBUILD_STORE", "").lower()
    rebuild_requested = env_rebuild in {"1", "true", "yes"}

    top_k_env = os.getenv("RECOMMENDER_TOP_K")
    try:
        top_k = int(top_k_env) if top_k_env else DEFAULT_TOP_K
    except ValueError:
        top_k = DEFAULT_TOP_K

    rebuild_store = rebuild_requested or not vector_store_exists
    if not rebuild_store and vector_store_exists and os.path.exists(sqlite_path):
        try:
            rebuild_store = os.path.getmtime(processed_csv_path) > os.path.getmtime(sqlite_path)
        except OSError:
            rebuild_store = True

    logger.info("Vector store rebuild requested: %s.", rebuild_store)

    recommender = Recommender(
        csv_file_path=processed_csv_path,
        persist_dir=persist_dir,
        rebuild_store=rebuild_store,
    )

    results = recommender.retrival(query, k=top_k)
    output = _format_results(results)
    print(output)
    logger.info("Recommendation run completed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
