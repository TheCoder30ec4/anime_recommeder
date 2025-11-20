import json
import os
from typing import List

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from utils.logger import get_logger

logger = get_logger(__name__)


class Llm:
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = 0
        self.max_retries = 3

    def instance(self) -> ChatGroq:
        return ChatGroq(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key,
            max_retries=self.max_retries,
        )

    def embedding_instance(self) -> HuggingFaceEmbeddings:
        if self.api_key:
            os.environ.setdefault("HUGGINGFACEHUB_API_TOKEN", self.api_key)

        preferred = os.getenv("EMBEDDING_DEVICE", "auto").strip().lower()
        devices_to_try = self._resolve_embedding_devices(preferred)
        last_error: Exception | None = None

        for device in devices_to_try:
            if device == "cuda" and not self._cuda_available():
                logger.debug("CUDA requested but unavailable; skipping GPU embedding load.")
                continue

            try:
                logger.info(
                    "Loading HuggingFace embeddings model '%s' on device '%s'.",
                    self.model_name,
                    device,
                )
                kwargs = {
                    "model_name": self.model_name,
                    "model_kwargs": {"device": device},
                    "encode_kwargs": {"device": device},
                }
                return HuggingFaceEmbeddings(**kwargs)
            except Exception as exc:  # pylint: disable=broad-except
                last_error = exc
                logger.warning(
                    "Failed to load embeddings model '%s' on device '%s': %s",
                    self.model_name,
                    device,
                    exc,
                )
        if last_error is not None:
            raise last_error
        return HuggingFaceEmbeddings(model_name=self.model_name)

    def tool_instance(self) -> ChatGroq:
        from pipeline.pipeline import run_anime_recommendations_tool

        tools = _get_shared_tools(run_anime_recommendations_tool)
        llm = ChatGroq(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key,
            max_retries=self.max_retries,
            
        )

        return llm.bind_tools(tools)

    @staticmethod
    def _cuda_available() -> bool:
        try:
            import torch

            return torch.cuda.is_available()
        except Exception:  # pylint: disable=broad-except
            return False

    @staticmethod
    def _resolve_embedding_devices(preferred: str) -> List[str]:
        if preferred in {"cuda", "gpu"}:
            return ["cuda", "cpu"]
        if preferred in {"cpu"}:
            return ["cpu"]
        if preferred in {"auto", ""}:
            return ["cuda", "cpu"]
        # If an arbitrary device string was provided (e.g., cuda:1), try it then fall back to CPU.
        return [preferred, "cpu"]


@tool("JSON", return_direct=True)
def _json_passthrough_tool(**kwargs) -> str:
    """Echo back the provided keyword arguments as a JSON string."""
    return json.dumps(kwargs)


@tool("json", return_direct=True)
def _json_passthrough_tool_lowercase(**kwargs) -> str:
    """Echo back the provided keyword arguments as a JSON string (lowercase variant for Groq compatibility)."""
    return json.dumps(kwargs)


@tool("commentary", return_direct=True)
def _commentary_passthrough_tool(**kwargs) -> str:
    """Allow models to return structured content via a commentary tool call."""
    return json.dumps(kwargs)


def _get_shared_tools(run_tool) -> List:
    return [run_tool, _json_passthrough_tool, _json_passthrough_tool_lowercase, _commentary_passthrough_tool]
