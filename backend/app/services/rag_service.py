import re

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.storage_service import StorageService


# Pattern to detect SCP numbers in user queries (e.g., "SCP-173", "scp 682")
SCP_PATTERN = re.compile(r"SCP[-\s]?(\d{3,4})", re.IGNORECASE)


def extract_scp_number(text: str) -> str | None:
    """Extract SCP designation from text, e.g. 'SCP-173'."""
    match = SCP_PATTERN.search(text)
    if match:
        number = match.group(1)
        return f"SCP-{number.zfill(3)}"
    return None


class RAGService:
    """SQLite Vector Similarity Search + Metadata Filtering."""

    def __init__(
        self,
        storage_service: StorageService,
        embedding_service: EmbeddingService,
    ):
        self.storage = storage_service
        self.embedding = embedding_service

    async def hybrid_search(
        self,
        query: str,
        item_number: str | None = None,
        object_class: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Perform vector similarity search via SQLite + NumPy.
        """
        # 1. Auto-detect SCP number from query
        detected_scp = extract_scp_number(query)
        if detected_scp and not item_number:
            item_number = detected_scp

        # 2. Embed the query
        query_vector = await self.embedding.encode(query)

        # 3. Execute search via StorageService (SQLite + NumPy)
        results = await self.storage.vector_search(
            query_vector=query_vector,
            top_k=top_k,
            item_number=item_number,
            object_class=object_class,
        )

        return results
