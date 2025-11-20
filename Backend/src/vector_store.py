import os
import shutil
from typing import Optional, Sequence

import pandas as pd
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from config.llm import Llm
from utils.logger import get_logger

load_dotenv()

hf_api: Optional[str] = os.getenv("HUGGING_FACE_API")

logger = get_logger(__name__)


class VectorStore:
    def __init__(self, csv_path: str, persist_dir: str = "VectorDataBase/chromaDB") -> None:
        self.csv_path = csv_path
        if not os.path.isabs(persist_dir):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
            persist_dir = os.path.join(project_root, persist_dir)
        os.makedirs(persist_dir, exist_ok=True)
        self.persist_dir = persist_dir
        self.embedding = Llm(model_name="all-MiniLM-L6-v2", api_key=hf_api)

    def Builder(self, force_rebuild: bool = False) -> None:
        logger.info(
            "Preparing vector store at '%s' (force_rebuild=%s).",
            self.persist_dir,
            force_rebuild,
        )
        if not force_rebuild and self._vector_store_exists():
            logger.info("Vector store already exists; skipping rebuild.")
            return

        df = pd.read_csv(self.csv_path, encoding="utf-8", on_bad_lines="skip")
        if df.empty:
            logger.error("Processed CSV '%s' produced no rows to index.", self.csv_path)
            raise ValueError("Processed CSV produced no rows to index.")

        text_column = "combined_info" if "combined_info" in df.columns else "sypnopsis"
        if text_column not in df.columns:
            logger.error(
                "Required text column missing in '%s'. Columns available: %s",
                self.csv_path,
                list(df.columns),
            )
            raise ValueError(
                "Expected a 'combined_info' or 'sypnopsis' column in the processed CSV."
            )

        documents: list[Document] = []
        metadata_fields: Sequence[str] = tuple(
            col for col in ("Name", "Score", "Genres") if col in df.columns
        )

        records = df.to_dict("records")
        for row in records:
            content = str(row.get(text_column, "") or "").strip()
            if not content:
                continue

            metadata = {}
            for field in metadata_fields:
                value = row.get(field, "")
                if pd.isna(value) or str(value).strip() == "":
                    continue
                metadata[field] = str(value).strip()

            documents.append(Document(page_content=content, metadata=metadata))

        if not documents:
            logger.error("No valid documents found to index from '%s'.", self.csv_path)
            raise ValueError("No valid documents found to index from the processed CSV.")

        # Remove any existing persisted store before re-creating to avoid stale data.
        if self._vector_store_exists():
            logger.info("Clearing existing vector store at '%s'.", self.persist_dir)
            self._clear_persisted_store()

        logger.info("Indexing %s documents into vector store.", len(documents))
        db = Chroma.from_documents(
            documents,
            self.embedding.embedding_instance(),
            persist_directory=self.persist_dir,
        )
        db.persist()
        logger.info("Vector store persisted at '%s'.", self.persist_dir)

    def load_vector_store(self):
        logger.debug("Loading vector store from '%s'.", self.persist_dir)
        return Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embedding.embedding_instance(),
        )

    def _vector_store_exists(self) -> bool:
        expected_sqlite = os.path.join(self.persist_dir, "chroma.sqlite3")
        expected_index = os.path.join(self.persist_dir, "index")
        return os.path.exists(expected_sqlite) or os.path.exists(expected_index)

    def _clear_persisted_store(self) -> None:
        if os.path.isdir(self.persist_dir):
            shutil.rmtree(self.persist_dir)
        os.makedirs(self.persist_dir, exist_ok=True)
